# ############################################## Module Information ####################################################
# Module              : businessLogic_patientPersistency
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# ######################################################################################################################

def business_logic(spark, src_input_tbl, cohort_input_tbl, index_dt_clmn, ntb_ntm_filter_vl, lookforward_option_vl,
                       persistency_period_vl,
                       level_rollup_clmns, cohort_grp_vl, num_ontherapy_threshold_vl, data_end_dt_vl, method_vl,
                       sob_rank_vl, include_grace_vl, denum_ontherapy_threshold_vl):
    level0_1 = level_rollup_clmns.split(",")
    level_rollup_clmns = " "
    level1 = " "
    level2 = " "
    level3 = " "
    level4 = " "
    level5 = " "
    level6 = " "
    level7 = " "
    # level0 = list(level0)
    for i in range(0, len(level0_1)):
        if (i == 0):
            level1 = level1 + "episode_cohort." + level0_1[i]
            level2 = level2 + "filtered_episode_rank." + level0_1[i]
            level3 = level3 + "persistent_flag." + level0_1[i]
            level4 = level4 + "persistent_period_end." + level0_1[i]
            level5 = level5 + "all_persistent_flag." + level0_1[i]
            level6 = level6 + "filtered_persistency_method." + level0_1[i]
            level7 = level7 + "persistency_dedup." + level0_1[i]
            # print(level0_1[i])
            level_rollup_clmns = level_rollup_clmns + level0_1[i]
        else:
            level1 = level1 + ",episode_cohort." + level0_1[i]
            level2 = level2 + ",filtered_episode_rank." + level0_1[i]
            level3 = level3 + ",persistent_flag." + level0_1[i]
            level4 = level4 + ",persistent_period_end." + level0_1[i]
            level5 = level5 + ",all_persistent_flag." + level0_1[i]
            level6 = level6 + ",filtered_persistency_method." + level0_1[i]
            level7 = level7 + ",persistency_dedup." + level0_1[i]
            level_rollup_clmns = level_rollup_clmns + "," + level0_1[i]

    patientPersistency_parameter_pass_check_v1 = ''' 
    ----** All flags are calculated and rolled up as per the persistent method selected  **----
select {level7}, patient_cohort, period_number,persistency_period, count(distinct case when patient_flag=1 then pat_gid else null end) as total_patient, 
count(case when persistent_flag='P' then persistent_flag else null end) as total_persistent_patient,count(case when persistent_flag='NC' then persistent_flag else null end) as total_non_compliant_patient,
count(case when persistent_flag='Drop' then persistent_flag else null end) as total_dropped_patient
from 
(
----** Deduped the records and select the persistent flag as per the method selected **----
    select {level6} ,pat_gid, period_number, persistency_period,patient_cohort,max(patient_flag) as patient_flag, max(case when period_number=0 then 'P' else persistent_flag end) as persistent_flag 
	from
	(
	 select {level5} ,pat_gid, period_number, persistency_period,patient_cohort, rnk, patient_flag, 
	 case when {method_vl}=2 then method2_persistent_flag 
	      when {method_vl}=3 then method3_persistent_flag 
		  when {method_vl}=4 then method4_persistent_flag 
		  when {method_vl}=5 then method5_persistent_flag 
	 end as persistent_flag 
	  from 
      (
	  ----** Method 3,4,5 is calculated from method 2 **----
        select {level4} ,pat_gid, period_number, available_lf,persistency_period,patient_cohort,rnk, patient_flag,
        
        
	    persistent_flag as method2_persistent_flag, 
	    case when patient_flag=1 and period_number <= max(last_episode_period_end) over (partition by pat_gid,rnk,{level4})
		     then 'P' 
		end as method3_persistent_flag,
	    case when patient_flag=1 and index_date = episode_start_date_drvd  and period_number <= max(first_episode_period_end) over (partition by pat_gid,index_date,rnk,{level4}) 
		     then 'P' 
	         when patient_flag=1 and period_number <= max(last_episode_period_end) over (partition by pat_gid,rnk,{level4}) 
			 then 'NC' 
		     when patient_flag=1 and period_number*30 <= available_lf 
			 then 'Drop' 
		end as method4_persistent_flag,
	    case when patient_flag=1 and index_date = episode_start_date_drvd  and period_number <= max(first_episode_period_end) over (partition by pat_gid,index_date,rnk,{level4}) 
		     then 'P' 
		end as method5_persistent_flag
	    from
	    ( 
		----** based on the lookforward_option and persistent flag, patient flag is calculated  **----
		  select 
		  {level3} , pat_gid, period_number, available_lf,rnk,episode_start_date_drvd,
		  persistency_period,patient_cohort,period_start_date,period_end_date,persistent_flag, index_date,
		  case when index_date = episode_start_date_drvd  and persistent_flag='P' then max(period_number) over (partition by pat_gid,index_date,episode_start_date_drvd,persistent_flag,rnk,{level3}) 
		       else -1 end as first_episode_period_end,
		  case when persistent_flag='P' then max(period_number) over (partition by pat_gid,persistent_flag,rnk,{level3}) else -1 end as last_episode_period_end,  	
		  case when lookforward_option='DYNAMIC' and persistent_flag='P' then 1 
		       when lookforward_option='DYNAMIC' and datediff(data_end_date,last_episode_end_date) >= grace and data_end_date >= date_add(period_start_date,denum_ontherapy_threshold) then 1 
			   when lookforward_option='DYNAMIC' and datediff(data_end_date,last_episode_end_date) < grace and datediff(least(last_episode_end_date,data_end_date),period_start_date) >=denum_ontherapy_threshold then 1 
			   when lookforward_option='FIXED' and available_lf >= persistency_period - grace then 1 else 0 
			   end as patient_flag
		  from 
	      (
		  ----** Persistent flag for method 2 is calculated by checking the episode overlap(provided in input) between period start date and period end date for a patient  **----
		    select 
		    {level2} , pat_gid, period_number, available_lf,rnk,episode_start_date_drvd,index_date,data_end_date,grace,episode_end_date1,denum_ontherapy_threshold,
		    persistency_period,patient_cohort,period_start_date,period_end_date,lookforward_option,
		    case when datediff(least (period_end_date,least(episode_end_date1,data_end_date)) , greatest(period_start_date,episode_start_date_drvd)) >= num_ontherapy_threshold and period_start_date < least (episode_end_date1,data_end_date) then 'P'  
                 else 'Drop' end as persistent_flag ,
             max(episode_end_date1) over (partition by pat_gid,rnk,{level2}) as last_episode_end_date 
		    from 
			    (
				 ----** Patients are time aligned to month 0, patient cohort is created and data is filtered as per the sob_rank provided in input  **----
				 
			      select {level1}, pat_gid, episode_start_date_drvd, episode_end_date1,index_date,data_end_date,grace,denum_ontherapy_threshold, period_number,episode_length,lookforward_option,persistency_period,num_ontherapy_threshold,rnk,sob_rank,
			      case 
			      	when cohort_grp='MONTHLY' then concat(month(index_date),'-',year(index_date))
			      	when cohort_grp='QUARTERLY' then concat((int((month(index_date)-1)/3)+1), '-', year(index_date))
			      	when cohort_grp='SEMESTERLY' then concat((int((month(index_date)-1)/6)+1),'-', year(index_date))
			      	when cohort_grp='ANNUALLY' then year(index_date) 
					when cohort_grp='OVERALL' then 'OVERALL' 
			      end as patient_cohort, 
			      date_add(index_date, (period_number)*30)    as period_start_date,
			      date_add(index_date, (period_number+1)*30) as period_end_date,
			      datediff(data_end_date,index_date) as available_lf
			       from 
			      (
				  ----** calculate index date, filtered rank from input table   **----
				    select {level_rollup_clmns}, patient_gid as pat_gid, to_date(from_unixtime(unix_timestamp(episode_start_date_drvd,'yyyy-MM-dd')))as episode_start_date_drvd,period_number, 
                    case when upper('{include_grace_vl}')='YES' then grace else 0 
                         end as grace,
				    	date_add(to_date(from_unixtime(unix_timestamp(episode_start_date_drvd,'yyyy-MM-dd'))),int(episode_length)) as episode_end_date1, 
				    	episode_length, upper('{cohort_grp_vl}') as  cohort_grp, upper('{lookforward_option_vl}') as lookforward_option, {persistency_period_vl} as persistency_period,rnk, '{sob_rank_vl}' as sob_rank,
				    	case when upper(spike5_pharmacy_flag)='Y' then to_date(from_unixtime(unix_timestamp(spike5_pharmacy_date,'yyyy-MM-dd'))) else to_date(from_unixtime(unix_timestamp({data_end_dt_vl},'yyyy-MM-dd'))) end as data_end_date,{num_ontherapy_threshold_vl} as num_ontherapy_threshold,{denum_ontherapy_threshold_vl} as denum_ontherapy_threshold,
				    	min (to_date(from_unixtime(unix_timestamp({index_dt_clmn},'yyyy-MM-dd')))) over (partition by patient_gid, rnk, {level_rollup_clmns})  as index_date,
				    	case when upper('{sob_rank_vl}')= 'FIRST' THEN min(rnk) over (partition by patient_gid,  {level_rollup_clmns}) 
				    	     when upper('{sob_rank_vl}')= 'LAST' then max(rnk) over (partition by patient_gid, {level_rollup_clmns}) 
				    	     when upper('{sob_rank_vl}')= 'ALL' then rnk 
				    	end as filtered_rank
				    from {src_input_tbl} sob
				    cross join 
				    (
					----** Manually maintained table, use to create period start date and period end date for a given episode start date  **----
				    	select int(period_number) as period_number from {cohort_input_tbl} where period_number<={persistency_period_vl}/30
				    ) cohort
				    where upper(ntb_flag) like upper('%{ntb_ntm_filter_vl}%') 
                --where pat_gid=100118600
			     )episode_cohort
			     where rnk=filtered_rank
		       )filtered_episode_rank
	       )persistent_flag
	    )persistent_period_end
      )all_persistent_flag
	)filtered_persistency_method
	group by {level_rollup_clmns},pat_gid, period_number, persistency_period,patient_cohort
)persistency_dedup
group by {level_rollup_clmns}, patient_cohort,period_number, persistency_period
'''.format(src_input_tbl=src_input_tbl, cohort_input_tbl=cohort_input_tbl, index_dt_clmn=index_dt_clmn,
           include_grace_vl=include_grace_vl,
           ntb_ntm_filter_vl=ntb_ntm_filter_vl, lookforward_option_vl=lookforward_option_vl,
           persistency_period_vl=persistency_period_vl, data_end_dt_vl=data_end_dt_vl,
           level_rollup_clmns=level_rollup_clmns, cohort_grp_vl=cohort_grp_vl,
           denum_ontherapy_threshold_vl=denum_ontherapy_threshold_vl,
           num_ontherapy_threshold_vl=num_ontherapy_threshold_vl, method_vl=method_vl, sob_rank_vl=sob_rank_vl,
           level1=level1, level2=level2, level3=level3, level4=level4, level5=level5, level6=level6, level7=level7)

    return spark.sql(patientPersistency_parameter_pass_check_v1)
