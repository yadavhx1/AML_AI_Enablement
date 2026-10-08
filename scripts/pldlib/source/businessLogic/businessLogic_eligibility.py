# ############################################## Module Information ####################################################
# Module              : businessLogic_eligibility
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# ######################################################################################################################

def determineCohort(frequency_vl):
    switcher = {
        "monthly": 1,
        "quarterly": 3,
        "semesterly": 6,
        "yearly": 12
    }
    return switcher[frequency_vl]


def business_logic(spark, index_dt_clmn, entity_input_tbl, activity_grain, activity_input_tbl, lb_ll_vl, lb_ul_vl,
                   lf_ll_vl, lf_ul_vl,
                   lb_th_vl,
                   lf_th_vl, frequency_vl, calendar_align_vl, sub_activity_type_vl, level_clmns, join_id_clmn):
    # if lb_ll_vl <= lb_ul_vl:
    # if lb_ul_vl <= lf_ll_vl:
    # if lf_ll_vl <= lf_ul_vl:
    # if lb_th_vl <= (lb_ul_vl - lb_ll_vl) / determineCohort(frequency_vl):
    # if lf_th_vl <= (lf_ul_vl - lf_ll_vl) / determineCohort(frequency_vl):
    level0_1 = level_clmns.split(",")
    level_clmns = " "
    level1 = " "
    level2 = " "
    level3 = " "
    level4 = " "
    level5 = " "
    level6 = " "
    # level_columns = list(level_clmns)
    for i in range(0, len(level0_1)):
        if (i == 0):
            level1 = level1 + "inp." + level0_1[i]
            level2 = level2 + "final_input." + level0_1[i]
            level3 = level3 + "pat_pool." + level0_1[i]
            level4 = level4 + "base." + level0_1[i]
            level5 = level5 + "cnt." + level0_1[i]
            level6 = level6 + "th_chk." + level0_1[i]
            # print(level0_1[i])
            level_clmns = level_clmns + level0_1[i]
        else:
            level1 = level1 + ",inp." + level0_1[i]
            level2 = level2 + ",final_input." + level0_1[i]
            level3 = level3 + ",pat_pool." + level0_1[i]
            level4 = level4 + ",base." + level0_1[i]
            level5 = level5 + ",cnt." + level0_1[i]
            level6 = level6 + ",th_chk." + level0_1[i]
            level_clmns = level_clmns + "," + level0_1[i]

    eligibility_onco_parameter_pass_check_v1 = spark.sql('''



Select {level6},TH_CHK.available_LB,TH_CHK.available_LF,TH_CHK.LB_valid_flag,TH_CHK.LF_valid_flag,TH_CHK.active_LB,active_LF,
case when TH_CHK.active_LB >= {lb_th_vl} then 1 else 0 end as LB_elig_flag,

case 
		when TH_CHK.active_LF >= {lf_th_vl} --(LF_Threshold)
		then 1 
		else 0 
	end as LF_elig_flag

from
	(
		------Counting active LB and LF periods in the analysis window-------	 
		Select {level5},CNT.adjusted_data_start, CNT.adj_INDEX_DT,CNT.adjusted_data_end,CNT.LB_st_dt,CNT.LB_end_dt,CNT.LF_st_dt,CNT.LF_end_dt,CNT.available_LB,CNT.available_LF,CNT.LB_valid_flag,CNT.LF_valid_flag,count(distinct CNT.count_LB) as active_LB,count(distinct CNT.count_LF )as active_LF

	from
		(
		 ------Counting period upto which data is available----
			Select  {level4},BASE.adj_index_dt,BASE.frequency,BASE.offset,BASE.lb_ll_vl,BASE.lb_ul_vl,BASE.lf_ll_vl,BASE.lf_ul_vl,BASE.freq_start_date_adj,BASE.adjusted_Data_start,BASE.adjusted_data_end,BASE.LB_st_dt,BASE.LB_end_dt,BASE.LF_st_dt,BASE.LF_end_dt,base.LB_valid_flag,base.LF_valid_flag,

				case when LB_valid_flag = 1 then 

					(case when ((BASE.LB_st_dt <= cast(BASE.freq_start_date_adj as date)) AND (cast(BASE.freq_start_date_adj as date) < BASE.LB_end_dt)) then BASE.freq_start_date_adj else null end)

				else 

					(case when (((BASE.adjusted_data_start <= cast(BASE.freq_start_date_adj as date)) AND (cast(BASE.freq_start_date_adj as date) < BASE.LB_end_dt))) then BASE.freq_start_date_adj else null end)

				end as count_LB,

				case when LF_valid_flag = 1 then

					(case when BASE.LF_st_dt <= cast(BASE.freq_start_date_adj as date) AND cast(BASE.freq_start_date_adj as date) < BASE.LF_end_dt then BASE.freq_start_date_adj else null end )
				else 
					(case when (BASE.LF_st_dt <= cast(BASE.freq_start_date_adj as date)) AND ((cast(BASE.freq_start_date_adj as date) < BASE.adjusted_data_end)) then BASE.freq_start_date_adj else null end )

				end as count_LF,

				case when base.LB_valid_flag = 1 then floor(months_between(BASE.LB_end_dt,BASE.LB_st_dt)/base.freq_weight)
				else floor(months_between(BASE.LB_end_dt,BASE.adjusted_data_start)/base.freq_weight) 
				end as available_LB,

				case when base.LF_valid_flag = 1
				then floor(months_between(BASE.LF_end_dt,BASE.LF_st_dt)/base.freq_weight)
				else floor(months_between(BASE.adjusted_data_end,BASE.LF_st_dt)/base.freq_weight)
				end as available_LF

		from
			(

				select {level3},min(calendar_align) as calendar_align,pat_pool.frequency,pat_pool.offset,pat_pool.adj_index_dt,pat_pool.lb_ll_vl,pat_pool.lb_ul_vl,pat_pool.lf_ll_vl,pat_pool.lf_ul_vl,pat_pool.adjusted_data_start,pat_pool.adjusted_data_end,pat_pool.LB_st_dt,pat_pool.LB_end_dt,pat_pool.LF_st_dt,pat_pool.LF_end_dt,pat_pool.freq_weight,

				case
					when pat_pool.freq_start_date < pat_pool.data_start then pat_pool.data_start
					when pat_pool.freq_start_date > pat_pool.data_end then pat_pool.data_end
				else freq_start_date
				end as freq_start_date_adj,

				case 
					when pat_pool.LB_st_dt >= pat_pool.adjusted_data_start   then 1 else 0 
				end as LB_valid_flag,
				Case 
					when pat_pool.LF_end_dt  <=  pat_pool.adjusted_data_end then 1 else 0 
				end as LF_valid_flag


			from
				(

				select {level2},FINAL_INPUT.index_dt,FINAL_INPUT.calendar_align,FINAL_INPUT.frequency,FINAL_INPUT.lb_ll_vl,FINAL_INPUT.lb_ul_vl,FINAL_INPUT.lf_ll_vl,FINAL_INPUT.lf_ul_vl,FINAL_INPUT.Offset,FINAL_INPUT.adj_index_dt,ACT_FNL.freq_start_date,ACT_FNL.Data_start,ACT_FNL.data_end, ACT_FNL.freq_weight,add_months(adj_index_dt,lb_ll_vl) as LB_st_dt, add_months(adj_index_dt,lb_ul_vl) as LB_end_dt, add_months(adj_index_dt,lf_ll_vl )as LF_st_dt, add_months(adj_index_dt,lf_ul_vl) as LF_end_dt,

				case 
					when Final_input.frequency = upper('monthly') then cast(from_unixtime(unix_timestamp(act_fnl.data_start, 'yyyyMMdd')) as date)
					when Final_input.frequency = upper('quarterly') and month(cast(act_fnl.data_start as date))%3 = 1 
					then cast(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%3)as date)
					when Final_input.frequency = upper('quarterly') and month(cast(act_fnl.data_start as date))%3 <> 1 
					then cast(ADD_MONTHS(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%3),3)as date)	 
					when Final_input.frequency = upper('semesterly') and month(cast(act_fnl.data_start as date))%6 = 1
					then cast(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%6)as date)
					when Final_input.frequency = upper('semesterly') and month(cast(act_fnl.data_start as date))%6 <> 1
					then cast(ADD_MONTHS(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%6),6)as date)	
					when Final_input.frequency = upper('yearly') and month(cast(act_fnl.data_start as date))%12 = 1 
					then cast(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%12)as date)
					when Final_input.frequency = upper('yearly') and month(cast(act_fnl.data_start as date))%12 <> 1  
					then cast(ADD_MONTHS(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_start ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%12),12)as date)
					else NULL 
				end as adjusted_data_start,


				case  
					when Final_input.frequency = upper('monthly') then cast(from_unixtime(unix_timestamp(act_fnl.data_end, 'yyyyMMdd')) as date)
					when Final_input.frequency = upper('quarterly') then cast(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_end ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_end ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%3)as date)
					when Final_input.frequency = upper('semesterly') then cast(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_end ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_end ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%6)as date)
					when Final_input.frequency = upper('yearly') then cast(ADD_MONTHS(from_unixtime(unix_timestamp( act_fnl.data_end ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(act_fnl.data_end ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%12)as date)
					else NULL
				end as adjusted_data_end  

				from
					(
					----** Calculation of offset and adjusting claim date as per calendar_align flag **----
						select {level1}, inp.index_dt,inp.Calendar_Align,inp.frequency,inp.lb_ll_vl,inp.lb_ul_vl,inp.lf_ll_vl,inp.lf_ul_vl,
						case when upper('{activity_grain}') = upper('monthly') then		
							(
							case 
								when Calendar_Align = upper('Yes') or Frequency = upper('monthly') then 0
								when Calendar_Align = upper('No') and Frequency = upper('quarterly') then month(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'))- month(ADD_MONTHS(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(index_dt ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%3))
								when Calendar_Align = upper('No') and Frequency = upper('semesterly') then  month(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01')) - month(ADD_MONTHS(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(index_dt ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%6))
								when Calendar_Align = upper('No') and Frequency = upper('yearly') then month(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01')) - month(ADD_MONTHS(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(index_dt ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%12))
								else null--UDF can be implemented to calculate quarter/semester and year start
							end
							)
							else 
							(
							case 
								WHEN Calendar_Align = upper('yes') or FREQUENCY = upper('quarterly') then 0 
								WHEN Calendar_Align = upper('No') and FREQUENCY = upper('semesterly') then (case when index_quarter%2 = 0 then 1 else 0 end)
								WHEN Calendar_Align = upper('No') and FREQUENCY = upper('yearly') then (index_quarter-1)
								else null
							end
							) 
						end as Offset, 

						case 
							when Calendar_Align = upper('No') or Frequency = upper('MONTHLY') then from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01')
							when Calendar_Align = upper('Yes') and Frequency = upper('quarterly') then ADD_MONTHS(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(index_dt ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%3)
							when Calendar_Align = upper('Yes') and Frequency = upper('semesterly') then ADD_MONTHS(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(index_dt ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%6)
							when Calendar_Align = upper('Yes') and Frequency = upper('yearly') then ADD_MONTHS(from_unixtime(unix_timestamp( index_dt  ,'yyyy-MM-dd' ),'yyyy-MM-01'),-1*(month(from_unixtime(unix_timestamp(index_dt ,'yyyy-MM-dd' ),'yyyy-MM-01'))-1)%12) --UDF can be implemented to calculate quarter/semester and year start
							else cast(index_dt as String)
						end as adj_index_dt

						from
							(
								----** Entity input table **----
								select {level_clmns},index_dt,
									case 
										when month_no in (1,2,3) then 1
										when month_no in (4,5,6) then 2
										when month_no in (7,8,9) then 3
									else 4 end as index_quarter,
								UPPER('{calendar_align_vl}') as calendar_align, UPPER('{frequency_vl}')as frequency,{lb_ll_vl} as lb_ll_vl,{lb_ul_vl} as lb_ul_vl,{lf_ll_vl} as lf_ll_vl,{lf_ul_vl} as lf_ul_vl
								from
								(
									select {level_clmns},cast({index_dt_clmn} as date) as index_dt, month(cast({index_dt_clmn} as date)) as month_no from {entity_input_tbl}  
								) Inp	

							)inp
					)FINAL_INPUT

					Left outer JOIN

					(
						  ----** Capturing all activities as per frequency **----
						select /*+ BROADCAST(dlim) */ Act.*,dlim.Data_start,dlim.data_end 
						from
							(
								select ACT.patient_gid,activity_date,Freq_start_date,offset,freq_weight
								from {activity_input_tbl} Act---Activity input table is hardcoded.
								where upper(frequency)=upper('{frequency_vl}') 
								and upper(sub_activity_type) = UPPER('{sub_activity_type_vl}')

							) Act 
							Cross JOIN 
							(	select min(cast(activity_date as date)) as Data_start, max(cast(activity_date as date)) as data_end
							   from {activity_input_tbl} ---Input Table is hardcoded; contains patient_activity_data
							)	dlim
					)Act_fnl ---** ACtivities Captured for patients **-----

					ON FINAL_INPUT.{join_id_clmn} = Act_fnl.{join_id_clmn}---this is hardcoded.will be taken as input from user as JOIN-ID.
					AND FINAL_INPUT.Offset = Act_fnl.Offset 
				)PAT_POOL---**LB and LF window calculated**---

			group by {level_clmns},adj_index_dt,frequency,offset,lb_ll_vl,lb_ul_vl,lf_ll_vl,lf_ul_vl,freq_start_date_adj,adjusted_Data_start,adjusted_data_end,LB_st_dt,LB_end_dt,LF_st_dt,LF_end_dt,freq_weight	
			)BASE	
		)CNT
		group by {level_clmns},adjusted_data_start,adjusted_data_end,adj_INDEX_DT,LB_st_dt,LB_end_dt,LF_st_dt,LF_end_dt,LB_valid_flag,LF_valid_flag,available_LB,available_LF
	)TH_CHK'''.format(entity_input_tbl=entity_input_tbl,
                      index_dt_clmn=index_dt_clmn,
                      activity_input_tbl=activity_input_tbl,
                      activity_grain=activity_grain,
                      sub_activity_type_vl=sub_activity_type_vl,
                      lb_ll_vl=lb_ll_vl,
                      lb_ul_vl=lb_ul_vl,
                      lf_ll_vl=lf_ll_vl,
                      lf_ul_vl=lf_ul_vl,
                      lb_th_vl=lb_th_vl,
                      lf_th_vl=lf_th_vl,
                      frequency_vl=frequency_vl,
                      calendar_align_vl=calendar_align_vl,
                      level_clmns=level_clmns,
                      level1=level1,
                      level2=level2,
                      level3=level3,
                      level4=level4,
                      level5=level5,
                      level6=level6,
                      join_id_clmn=join_id_clmn))

    return eligibility_onco_parameter_pass_check_v1

#                   else:
#                     print("Lookforward Threshold should be less than available frequencies")
#                       return None
#               else:
#                   print("Lookbackward Threshold should be less than available frequencies")
#                   return None
#
#           else:
#              print("The condition " + "lf_ll_vl = " + str(lf_ll_vl) + " <= lf_ul_vl = " + str(lf_ul_vl))
#              return None
#     else:
#        print("The condition " + "lb_ll_vl = " + str(lb_ll_vl) + " <= lb_ul_vl = " + str(lb_ul_vl))
#       return None
#
# else:
#   print("The condition " + "lb_ul_vl = " + str(lb_ul_vl) + " <= lf_ll_vl = " + str(lf_ll_vl))
#  return None
