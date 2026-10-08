# ############################################## Module Information ####################################################
# Module              : businessLogic_episodePersistency
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# #####################################################################################################################

def business_logic(spark, cohort_grp_vl, cohort_input_tbl, src_input_tbl, data_end_date_vl, index_dt_clmn,
                       lookforward_option_vl, persistency_period_vl, level_rollup_clmns):
    level0_1 = level_rollup_clmns.split(",")
    level_rollup_clmns = " "
    level1 = " "
    level2 = " "
    level3 = " "
    level4 = " "
    for i in range(0, len(level0_1)):
        if (i == 0):
            level1 = level1 + "SRC." + level0_1[i]
            level2 = level2 + "FLGS." + level0_1[i]
            level3 = level3 + "TOTALS." + level0_1[i]
            level4 = level4 + "FNL." + level0_1[i]
            level_rollup_clmns = level_rollup_clmns + level0_1[i]
        else:
            level1 = level1 + ",SRC." + level0_1[i]
            level2 = level2 + ",FLGS." + level0_1[i]
            level3 = level3 + ",TOTALS." + level0_1[i]
            level4 = level4 + ",FNL." + level0_1[i]
            level_rollup_clmns = level_rollup_clmns + "," + level0_1[i]
    eligibility_onco_parameter_pass_check_v1 = '''select period_number,cohort_grp_value,{level4},sum(total_episode_flag) as total_episodes,sum(persistent_fnl_flag) as persistent_episodes
from(
    ----** Flagging patients for each period number for total_episode_flag and persistent_flag----**
		select TOTALS.patient_gid, {level3},TOTALS.persistent_flag,TOTALS.total_episode_flag,TOTALS.period_number,TOTALS.cohort_grp_value,
			case when TOTALS.total_episode_flag = 1 and TOTALS.persistent_flag = 1 then 1 else 0 end as persistent_fnl_flag 
	from (
	----** Total episode flag is calculated according to the lookforward option specified in parameter **------

				select FLGS.patient_gid,FLGS.{index_dt_clmn},FLGS.episode_end_date, {level2},FLGS.episode_len,FLGS.cohort_grp_value,FLGS.period_start_dt,FLGS.period_end_dt,FLGS.period_number,
					case when 
						 period_end_dt <= date_add({index_dt_clmn},int(episode_len))
						 then 1 else 0 
					end as persistent_flag,
					case when	
						 upper('{lookforward_option_vl}') = upper('dynamic') and period_end_dt <= date_add({index_dt_clmn},LF_available)
						 then 1 
						 when upper('{lookforward_option_vl}') = upper('fixed') and LF_available >= {persistency_period_vl}
						 then 1
						 else 0 
					end as total_episode_flag 
		from ( 
		-----** Cross join Source Table with cohort table upto persistency period with calculation of available lookforward **------------------
						select SRC.patient_gid,{level1},from_unixtime(unix_timestamp( SRC.episode_st_date ,'yyyy-MM-dd' ),'yyyy-MM-dd') as episode_st_date,
						date_add(from_unixtime(unix_timestamp(SRC.episode_st_date,'yyyy-MM-dd'),'yyyy-MM-dd'),episode_len )as episode_end_date, SRC.episode_len,
						  case when upper('{cohort_grp_vl}') = upper('monthly') 
								then concat(int(month({index_dt_clmn})),-int(year({index_dt_clmn})))
								when upper('{cohort_grp_vl}') = upper('quarterly') 
								then concat('q',int((month({index_dt_clmn})-1)/3)+1,-int(year({index_dt_clmn})))
								when upper('{cohort_grp_vl}') = upper('semesterly' )
								then  concat('s',int((month({index_dt_clmn})-1)/6)+1,-int(year({index_dt_clmn})))
								when upper('{cohort_grp_vl}') = upper('yearly') 
								then int(year({index_dt_clmn}))
								else 'overall'
						  end as cohort_grp_value,CRT.period_number,{index_dt_clmn} as period_start_dt,date_add({index_dt_clmn},period_number) as period_end_dt, datediff('{data_end_date_vl}',{index_dt_clmn}) as LF_available
					    from {src_input_tbl} SRC 
						
						cross join 
				 
				 ( -----** This table has rows of days **-----
					 select period_number 
					 from {cohort_input_tbl} CRT 
					 where period_number <= {persistency_period_vl}
				 )CRT
			)FLGS
	   )TOTALS
 )FNL
  group by {level_rollup_clmns},period_number,cohort_grp_value'''.format(src_input_tbl=src_input_tbl,
                                                                          index_dt_clmn=index_dt_clmn,
                                                                          cohort_input_tbl=cohort_input_tbl,
                                                                          lookforward_option_vl=lookforward_option_vl,
                                                                          cohort_grp_vl=cohort_grp_vl,
                                                                          persistency_period_vl=persistency_period_vl,
                                                                          level_rollup_clmns=level_rollup_clmns,
                                                                          data_end_date_vl=data_end_date_vl,
                                                                          level1=level1,
                                                                          level2=level2,
                                                                          level3=level3,
                                                                          level4=level4)

    return spark.sql(eligibility_onco_parameter_pass_check_v1)
