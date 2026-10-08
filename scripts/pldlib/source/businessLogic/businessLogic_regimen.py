# ############################################## Module Information ####################################################
# Module              : businessLogic_regimen
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# ######################################################################################################################


def business_logic(spark, **kwargs):
    regimen_immun_parameter_pass_check_v1 = spark.sql('''
--------------------------------------------------
--Module Name :-   MABI_PLD_REGIMEN_TBL
--Module description : - This module will create Regimens 
--Parameters required :- Databasename, Tablename, Regimen Threshold, Episode Start Date, Episode End Date
--Created by :- ABHISAX
--Created on :- 15 Dec 2018
--Version History :- N/A
---------------------------------------------------

--**Updating regimens which are lesser than threshold, no gap to next regimen and is not the last regimen for the patient **--
select 
patient_gid_rgmn
,final_indication_drvd
,regimen_start_date
,regimen_end_date
,regimen_threshold
,regimen_length
,regimen_threshold_flag
,regimen_remove_flag
,regimen_valid_flag
,clean_up_type
,gap_to_next_regimen
--,regimen_removal
,regimen
,drug_regimen
,drug_regimen_2
,case 
   when regimen_threshold_flag=1 
      and gap_to_next_regimen=0 
      and to_date(regimen_end_date)<to_date(max(regimen_end_date) over (partition by patient_gid_rgmn))
   then max(regimen) over (partition by patient_gid_rgmn order by to_date(regimen_start_date),to_date(regimen_end_date) rows between 1 following and 1 following) 
   else regimen 
end as updated_regimen

,case 
   when regimen_threshold_flag=1 
      and gap_to_next_regimen=0 
      and to_date(regimen_end_date)<to_date(max(regimen_end_date) over (partition by patient_gid_rgmn))
   then max(drug_regimen) over (partition by patient_gid_rgmn order by to_date(regimen_start_date),to_date(regimen_end_date) rows between 1 following and 1 following) 
   else drug_regimen 
end as updated_drug_regimen

,case 
   when regimen_threshold_flag=1 
      and gap_to_next_regimen=0 
      and to_date(regimen_end_date)<to_date(max(regimen_end_date) over (partition by patient_gid_rgmn))
   then max(drug_regimen_2) over (partition by patient_gid_rgmn order by to_date(regimen_start_date),to_date(regimen_end_date) rows between 1 following and 1 following) 
   else drug_regimen_2 
end as updated_drug_regimen_2



from
(
--**Creating drug regimen from product regimen and calculating gap to next regimen**--

select 
patient_gid_rgmn
,final_indication_drvd
,regimen_start_date
,regimen_end_date
,regimen_threshold
,regimen_length
,regimen_threshold_flag
,regimen_remove_flag
,regimen_valid_flag
,clean_up_type
,datediff(max(regimen_start_date) over (partition by patient_gid_rgmn order by to_date(regimen_start_date),to_date(regimen_end_date) rows between 1 following and 1 following),to_date(regimen_end_date)) as gap_to_next_regimen
--,case when clean_up_type='yesremove' and regimen_remove_flag=1 then 1 else 0 end as regimen_removal
,regimen
,drug_regimen

,regexp_replace({regimen_replace_clmn},{product_replace_from_vls},{product_replace_to_vls}) as drug_regimen_2

from 
(
--**Flagging regimens with clean up type as yes and are smaller than threshold. These regimens would later be filtered out in the process. Creating valid and invalid regimen flags based on whether the current along with previous or next regimen is smaller than threshold**--

select 
 patient_gid_rgmn
,final_indication_drvd
,regimen_start_date
,regimen_end_date
,regimen_threshold
,regimen_length
,regimen_threshold_flag
,clean_up_type



,case 
   when clean_up_type like 'yes%' and regimen_threshold_flag=1 
      then 1 
      else 0 
   end as regimen_remove_flag
   
,case 
   when (regimen_threshold_flag=1) and 
   (max(regimen_threshold_flag) over (partition by patient_gid_rgmn order by to_date(regimen_start_date),to_date(regimen_end_date) rows between 1 following and 1 following)=1  
      or max(regimen_threshold_flag) over (partition by patient_gid_rgmn order by to_date(regimen_start_date),to_date(regimen_end_date) rows between 1 preceding and 1 preceding)=1)
   then 'Invalid' 
   else 'Valid' 
end as regimen_valid_flag
,regimen
,drug_regimen

from
(
--**Creating flag for regimens against threshold value and also defining regimens**--
-- collect_type_rgmn_vl and collect_type_drg_rgmn_vl will be used to consider or not consider duplicates in the regimen name --

select 
 patient_gid_rgmn
,final_indication_drvd
,regimen_start_date
,regimen_end_date
,regimen_threshold
,clean_up_type
,datediff(regimen_end_date,regimen_start_date) as regimen_length
,case 
   when (datediff(regimen_end_date,regimen_start_date))<regimen_threshold 
   then 1 
   else 0 
 end as regimen_threshold_flag

,concat_ws(', ',sort_array({collect_type_rgmn_vl}(product_name_rgmn))) as regimen
,concat_ws(', ',sort_array({collect_type_drg_rgmn_vl}(drug_class_rgmn))) as drug_regimen
--Specific values for collect_type are collect_set or collect_list

from
(
--**Filtering for valid regimens**--
select 
 patient_gid_rgmn
,product_name_rgmn
,drug_class_rgmn
,final_indication_drvd
,regimen_start_date
,regimen_end_date
,regimen_threshold
,clean_up_type

from
(
--**Getting Episode columns and creating regimen mid date to keep only valid regimens**--
select 
 rgmn_dts.patient_gid_rgmn
,epsd_tbl.product_name_rgmn
,epsd_tbl.drug_class_rgmn
,rgmn_dts.final_indication_drvd
,rgmn_dts.regimen_start_date
,rgmn_dts.regimen_end_date
,epsd_tbl.{episode_start_dt_clmn}
,epsd_tbl.{episode_end_dt_clmn}
,rgmn_dts.regimen_threshold
,rgmn_dts.clean_up_type
,cast(FROM_UNIXTIME(UNIX_TIMESTAMP(date_add(regimen_start_date,cast((0.5*datediff(regimen_end_date,regimen_start_date)) as int)),'yyyy-MM-dd'),'yyyy-MM-dd 00:00:00') as timestamp) as reg_mid_dt
from
(
--**Creating regimen end date**--

select patient_gid_rgmn
,dt as regimen_start_date
,final_indication_drvd
,coalesce(max(dt) over(partition by patient_gid_rgmn order by dt rows between 1 following and 1 following),
cast(from_unixtime(unix_timestamp( '{data_end_dt_vl}'  ,'yyyy-MM-dd' ),'yyyy-MM-dd 00:00:00') as timestamp)) as regimen_end_date
,regimen_threshold
,clean_up_type
from
(
--**Define Regimen threshold and Regimen Clean Up Type**--

select patient_gid_rgmn
,dt
,final_indication_drvd
,'{regimen_threshold_vl}' as regimen_threshold
,'{clean_up_type_vl}' as clean_up_type 
--clean_up_type options are no, yes 

from
(
--**Source Data**--
--**Union Episode Start and Episode End Date in single column for the purpose of creating regimen**--

select {patient_gid_clmn} as patient_gid_rgmn,{episode_start_dt_clmn} as dt
,{final_indication} as final_indication_drvd
from {src_input_tbl} as src_ip 
where to_date({episode_start_dt_clmn})<> to_date({episode_end_dt_clmn})
and {episode_end_dt_clmn} is not null

union all

select {patient_gid_clmn} as patient_gid_rgmn,{episode_end_dt_clmn} as dt
--Episode End Date is parameterized to consider any End date from the episode table 
,{final_indication} as  final_indication_drvd
from {src_input_tbl} as src_ip
where to_date({episode_start_dt_clmn})<> to_date({episode_end_dt_clmn})
and {episode_end_dt_clmn} is not null


)dt_mrg
group by patient_gid_rgmn,final_indication_drvd ,dt
)rgmn_thrshld_dfn
)rgmn_dts

left join 
(
--**Episode Table **--
select 
{product_name_clmn} as product_name_rgmn
,{drug_class_clmn} as drug_class_rgmn
,{episode_start_dt_clmn}
,{episode_end_dt_clmn}
,{patient_gid_clmn} as patient_gid_epsd
from {src_input_tbl} as src_ip 
where {episode_end_dt_clmn} is not null
)epsd_tbl
on rgmn_dts.patient_gid_rgmn=epsd_tbl.patient_gid_epsd
)rgmn_mid_dt
where to_date(reg_mid_dt)>=to_date({episode_start_dt_clmn}) and to_date(reg_mid_dt)<to_date({episode_end_dt_clmn})
)rgmn_rnk
group by patient_gid_rgmn
,final_indication_drvd
,regimen_start_date
,regimen_end_date
,regimen_threshold
,clean_up_type
)rgmn_crtn
)rgmn_flgs
)rgmn_gap_remvl
where regimen_remove_flag in ({regimen_removal_vl})
'''.format(**kwargs))

    return regimen_immun_parameter_pass_check_v1
