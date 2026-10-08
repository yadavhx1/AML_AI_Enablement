# ############################################## Module Information ####################################################
# Module              : businessLogic_compliance
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : compliance
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# ######################################################################################################################


def business_logic(spark, **kwargs):
    compliance_module = spark.sql('''
--------------------------------------------------
--Module Name :-   MABI_PLD_COMPLIANCE_TBL
--Module description : - This module will create weighted and non-weighted compliance 
--Parameters required :- 
--Created by :- ABHISAX
--Created on :- 15 Nov 2018
--Version History :- N/A
---------------------------------------------------


--** Calculate weighted and non weighted compliance **--
select {roll_up_lvl_clmns},ntb_rnk
, sum(dos_w_index_roll_sngl) as total_dos_trim
, sum(dot_w_index_roll_sngl) as total_length_trim
, max(time_range_roll_sngl) as time_range_trim
, sum(dos_w_index_roll_sngl_f_dos) as total_dos_full
, sum(dot_w_index_roll_sngl_f_dos) as total_length_full
, max(time_range_roll_sngl_f_dos) as time_range_full
,case 
   when sum(dos_w_index_roll_sngl) is null or sum(dot_w_index_roll_sngl) is null 
   then null 
   when sum(dot_w_index_roll_sngl)=0 
   then 0
   when sum(dos_w_index_roll_sngl)  - sum(dot_w_index_roll_sngl) > 0
   then 1
   else 
   cast(sum(dos_w_index_roll_sngl) as decimal (22,7))/ cast(sum(dot_w_index_roll_sngl) as decimal(22,7))
end as cmplnc_dos_dot_wghtd

,case 
   when sum(dos_w_index_roll_sngl) is null or max(time_range_roll_sngl) is null 
   then null
   when max(time_range_roll_sngl)=0
   then 0 
   when sum(dos_w_index_roll_sngl) - max(time_range_roll_sngl) > 0
   then 1
   else 
   cast(sum(dos_w_index_roll_sngl) as decimal (22,7))/ max(time_range_roll_sngl) 
end as cmplnc_dos_tm_rng_wghtd

,case 
   when sum(dot_w_index_roll_sngl) is null or max(time_range_roll_sngl) is null 
   then null
   when max(time_range_roll_sngl)=0 
   then 0
   when sum(dot_w_index_roll_sngl)  - max(time_range_roll_sngl) >0
   then 1
   else
   cast(sum(dot_w_index_roll_sngl) as decimal (22,7))/ max(time_range_roll_sngl) 
end as cmplnc_dot_tm_rng_wghtd


,case 
   when sum(dos_w_index_roll_sngl_f_dos) is null or sum(dot_w_index_roll_sngl_f_dos) is null 
   then null
   when sum(dot_w_index_roll_sngl_f_dos)=0 
   then 0
   when sum(dos_w_index_roll_sngl_f_dos)  - sum(dot_w_index_roll_sngl_f_dos) > 0
   then 1
   else 
   cast(sum(dos_w_index_roll_sngl_f_dos) as decimal (22,7)) / cast(sum(dot_w_index_roll_sngl_f_dos) as decimal (22,7))
end as cmplnc_dos_dot_wghtd_f_dos

,case 
   when sum(dos_w_index_roll_sngl_f_dos) is null or max(time_range_roll_sngl_f_dos) is null 
   then null
   when max(time_range_roll_sngl_f_dos)=0 
   then 0
   when sum(dos_w_index_roll_sngl_f_dos) - max(time_range_roll_sngl_f_dos) > 0
   then 1
   else 
   cast(sum(dos_w_index_roll_sngl_f_dos) as decimal (22,7))/max(time_range_roll_sngl_f_dos) 
end as cmplnc_dos_tm_rng_wghtd_f_dos

,case 
   when sum(dot_w_index_roll_sngl_f_dos) is null or max(time_range_roll_sngl_f_dos) is null 
   then null 
   when max(time_range_roll_sngl_f_dos)=0
   then 0
   when sum(dot_w_index_roll_sngl_f_dos) -  max(time_range_roll_sngl_f_dos) >0
   then 1
   else
   cast(sum(dot_w_index_roll_sngl_f_dos) as decimal (22,7))/ max(time_range_roll_sngl_f_dos)
end as cmplnc_dot_tm_rng_wghtd_f_dos

,case when sum(cmplnc_dos_dot) is null then null else cast(avg(cmplnc_dos_dot) as decimal (22,7)) end as cmplnc_dos_dot_non_wghtd

,case when sum(cmplnc_dos_time_range) is null then null else cast(avg(cmplnc_dos_time_range) as decimal (22,7)) end as cmplnc_dos_tm_rng_non_wghtd

,case when sum(cmplnc_dot_time_range) is null then null else cast(avg(cmplnc_dot_time_range) as decimal (22,7)) end as cmplnc_dot_tm_rng_non_wghtd

,case when sum(cmplnc_dos_dot_f_dos) is null then null else cast(avg(cmplnc_dos_dot_f_dos) as decimal (22,7)) end as cmplnc_dos_dot_non_wghtd_f_dos

,case when sum(cmplnc_dos_time_range_f_dos) is null then null else cast(avg(cmplnc_dos_time_range_f_dos) as decimal (22,7)) end as cmplnc_dos_tm_rng_non_wghtd_f_dos

,case when sum(cmplnc_dot_time_range_f_dos) is null then null else cast(avg(cmplnc_dot_time_range_f_dos) as decimal (22,7)) end as cmplnc_dot_tm_rng_non_wghtd_f_dos

from
(
--** Pick required columns for rollup **--
select 
 {roll_up_lvl_clmns}
,episode_num_drvd, ntb_rnk, 
 dos_w_index_roll, time_range_roll, dos_w_index_roll_f_dos, time_range_roll_f_dos, cmplnc_dos_dot, cmplnc_dos_time_range, cmplnc_dot_time_range, cmplnc_dos_dot_f_dos, cmplnc_dos_time_range_f_dos, cmplnc_dot_time_range_f_dos, dos_w_index_roll_sngl, dot_w_index_roll_sngl, time_range_roll_sngl, dos_w_index_roll_sngl_f_dos, dot_w_index_roll_sngl_f_dos, time_range_roll_sngl_f_dos
from
(
--** Calculate DOS/ DOT, DOS/ Time Range, DOT/ Time Range compliance **--

select metrics_rolled.*
,case 
   when dot_w_index=0 or dot_w_index is null
   then null 
   else dos_w_index_roll
      /
      dot_w_index
end as cmplnc_dos_dot

,case 
   when time_range_roll=0 or time_range_roll is null
   then null
   else dos_w_index_roll
      /
      time_range_roll
end as cmplnc_dos_time_range 

,case 
   when time_range_roll=0 or time_range_roll is null
   then null
   else dot_w_index
      /
      time_range_roll 
end as cmplnc_dot_time_range


,case 
   when dot_w_index_f_dos=0 or dot_w_index_f_dos is null
   then null 
   when dos_w_index_roll_f_dos-dot_w_index_f_dos>0
   then 1
   else dos_w_index_roll_f_dos
      /
      dot_w_index_f_dos
end as cmplnc_dos_dot_f_dos

,case 
   when time_range_roll_f_dos=0 or time_range_roll_f_dos is null
   then null
   when dos_w_index_roll_f_dos-time_range_roll_f_dos>0
   then 1
   else dos_w_index_roll_f_dos
      /
      time_range_roll_f_dos
end as cmplnc_dos_time_range_f_dos 

,case 
   when time_range_roll_f_dos=0 or time_range_roll_f_dos is null
   then null
   when dot_w_index_f_dos-time_range_roll_f_dos>0
   then 1
   else dot_w_index_f_dos
      /
      time_range_roll_f_dos 
end as cmplnc_dot_time_range_f_dos


,case when roll_up_column=1 then dos_w_index_roll else 0 end as dos_w_index_roll_sngl
,case when roll_up_column=1 then dot_w_index else 0 end as dot_w_index_roll_sngl
,case when roll_up_column=1 then time_range_roll else 0 end as time_range_roll_sngl
,case when roll_up_column=1 then dos_w_index_roll_f_dos else 0 end as dos_w_index_roll_sngl_f_dos
,case when roll_up_column=1 then dot_w_index_f_dos else 0 end as dot_w_index_roll_sngl_f_dos
,case when roll_up_column=1 then time_range_roll_f_dos else 0 end as time_range_roll_sngl_f_dos


from

(
--** Calculate Roll up dos and max of Timerange **--
select mtrcs.*
,sum(dos_w_index) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as dos_w_index_roll
,max(time_range) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as time_range_roll

,sum(dos_w_index_f_dos) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as dos_w_index_roll_f_dos
,max(time_range_f_dos) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as time_range_roll_f_dos


from
(
--** Calculate dos, dot and time range with full dos and trim dos for last claim considered or not cases **--
--**--
--dos calculation- 
--Last claim considered- If claim starts beyond index_end_date then 0, if index end cuts the claim then dos will be claim start date to index start date else considered dos 
--Last claim not considered- If last claim or claim starts beyond index end date then 0, when index end cuts the claim then dos will be claim start date to index start date else consider dos
-- 
--dot calculation-
--Last claim considered- If single claim in the episode then null, if episode starts beyond index end date then 0, if index cuts episode then dot will be episode start to index end else consider episode length
--Last claim not considered- If single claim in the episode then null, if episode starts beyond index end date then 0, if index cuts episode (considered leaving last claim ie episode date 3) then dot will be episode start to index end else consider episode length by removing dos of all last claims
--
--Time range calculation-
--Last claim considered- Consider modified lookforward as time range
--Last claim not considered- If index end cuts last claim then considered mod lookforward - gap between claim start and index end else subtract dos of all last claim from the lookforward
--**--

--** Create an identifier to keep only 1 row for an episode. This will help in considering single values for fields where data is replicated at episode level **--


select ntb_rnkng.*

--**dos dot time range values**--
,case 
   when last_claim_cnsdr='yes'
   then 
      case 
         when (date_add(index_date,0) > date_add(claim_end_date_w_trim_dos,0)) or (date_add(index_end_date,0) < date_add(claim_date_mod,0) )
         then 0
         when date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0) 
         then datediff(date_add(index_end_date,0), date_add(claim_date_mod,0)) 
         when date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0)
         then datediff(date_add(claim_end_date_w_trim_dos,0),date_add(index_date,0))
         when (date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0)) and (date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0) )
         then datediff(date_add(index_end_date,0),date_add(index_date,0))
         else dos_trim
      end 
   when  last_claim_cnsdr='no'
      then 
         case 
            when (last_claim_idntfr=1) or (date_add(index_end_date,0) < date_add(claim_date_mod,0)) or (date_add(index_date,0) > date_add(claim_end_date_w_trim_dos,0))
            then 0
            when date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0) 
            then datediff(date_add(index_end_date,0), date_add(claim_date_mod,0))
            when date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0) 
            then datediff(date_add(claim_end_date_w_trim_dos,0),date_add(index_date,0))
            when (date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0)) 
            and (date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0) )
            then datediff(date_add(index_end_date,0),date_add(index_date,0)) 
            else dos_trim
         end
end as dos_w_index


,case 
   when last_claim_cnsdr='yes'
   then 
      case 
         when (date_add(index_date,0) > date_add(claim_end_date_w_dos,0)) or (date_add(index_end_date,0) < date_add(claim_date_mod,0)) 
         then 0
         when (date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0)) 
         and (date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0) )
         then datediff(date_add(index_end_date,0),date_add(index_date,0))
         when date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0) 
         then datediff(date_add(index_end_date,0), date_add(claim_date_mod,0)) 
         when date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0) 
         then datediff(date_add(claim_end_date_w_dos,0),date_add(index_date,0))
         else dos_drvd
      end 
   when  last_claim_cnsdr='no'
      then 
         case 
            when (last_claim_idntfr=1) or (date_add(index_end_date,0) < date_add(claim_date_mod,0)) or (date_add(index_date,0) > date_add(claim_end_date_w_dos,0))
            then 0
            when (date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0)) 
            and (date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0) )
            then datediff(date_add(index_end_date,0),date_add(index_date,0))            
            when date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0) 
            then datediff(date_add(index_end_date,0), date_add(claim_date_mod,0)) 
            when date_add(index_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_dos,0) 
            then datediff(date_add(claim_end_date_w_dos,0),date_add(index_date,0))
            else dos_drvd
         end
end as dos_w_index_f_dos



,case 
   when last_claim_cnsdr='yes'
      then 
         case
            when episode_end_date3_drvd is null 
            then null
            when (date_add(index_date,0) > date_add(episode_end_date1_drvd,0)) or (date_add(index_end_date,0) < date_add(episode_start_date_drvd,0))
            then 0
            when (date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0)) 
            and (date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0))
            then datediff(index_end_date,index_date)
            when date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd ,0) --End Date 1 till claim end date. End Date 2 is dos+grace
            then datediff(date_add(index_end_date,0) , date_add(episode_start_date_drvd,0))
            when date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0)
            then datediff(date_add(episode_end_date1_drvd,0),date_add(index_date,0))
            else episode_length 
         end
      when last_claim_cnsdr='no' 
      then 
         case 
            when episode_end_date3_drvd is null 
            then null
            when (date_add(index_end_date,0) < date_add(episode_start_date_drvd,0)) or (date_add(index_date,0) > date_add(episode_end_date3_drvd,0))
            then 0
            --**Check with date_add(episode_end_date3_drvd,0) for condition when last claim is not considered. Compliance should be null when 1 claim**--
            when (date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0)) and (date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0))
            then datediff (date_add(index_end_date,0),date_add(index_date,0))
            when date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0)
            then datediff(date_add(index_end_date,0) , date_add(episode_start_date_drvd,0)) 
            when date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0)
            then datediff (date_add(episode_end_date3_drvd,0), date_add(index_date,0))
            else episode_length - sum(case when last_claim_idntfr=1 then dos_trim else 0 end) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)
         end
end as dot_w_index       



,case 
   when last_claim_cnsdr='yes'
      then 
         case 
            when episode_end_date3_drvd is null 
            then null
            when (date_add(index_date,0) > date_add(episode_end_date1_drvd,0)) or (date_add(index_end_date,0) < date_add(episode_start_date_drvd,0))
            then 0
            when (date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0)) and (date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0))
            then datediff(date_add(index_end_date,0),date_add(index_date,0))
            when date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0)  --End Date 1 till claim end date. End Date 2 is dos+grace
            then datediff(date_add(index_end_date,0) , date_add(episode_start_date_drvd,0)) 
            when date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date1_drvd,0)  
            then datediff(date_add(episode_end_date1_drvd,0),date_add(index_date,0))
            else episode_length 
         end
      when last_claim_cnsdr='no' 
      then 
         case 
            when episode_end_date3_drvd is null 
            then null
            when (date_add(index_end_date,0) < date_add(episode_start_date_drvd,0)) or (date_add(index_date,0) > date_add(episode_end_date3_drvd,0))
            then 0
            --**Check with episode_end_date3_drvd for condition when last claim is not considered. Compliance should be null when 1 claim**--
            when (date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0)) and (date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0))
            then datediff (date_add(index_end_date,0),date_add(index_date,0))
            when date_add(index_end_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0)
            then datediff(date_add(index_end_date,0) , date_add(episode_start_date_drvd,0)) 
            when date_add(index_date,0) between date_add(episode_start_date_drvd,0) and date_add(episode_end_date3_drvd,0)
            then datediff (date_add(episode_end_date3_drvd,0), date_add(index_date,0))
            else episode_length - sum(case when last_claim_idntfr=1 then dos_drvd else 0 end) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)
         end
end as dot_w_index_f_dos


,case 
   when last_claim_cnsdr='yes'
   then
      case 
         when last_claim_idntfr=1 
         then lookforward_mod 
         else 0
      end 
   when last_claim_cnsdr='no'
   then 
      case 
         when last_claim_idntfr=1 and (date_add(index_end_date,0) between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0))
         then lookforward_mod - datediff(date_add(index_end_date,0), date_add(claim_date_mod,0))
         when last_claim_idntfr=1 and (date_add(index_end_date,0) not between date_add(claim_date_mod,0) and date_add(claim_end_date_w_trim_dos,0))
         then lookforward_mod - sum(case when last_claim_idntfr=1 then dos_trim else 0 end) over (partition by {patient_gid_clmn},{product_name_clmn},ntb_rnk)
         else 0
      end 
end as time_range

,case 
   when last_claim_cnsdr='yes'
   then
      case 
         when last_claim_idntfr=1 
         then lookforward_mod 
         else 0
      end 
   when last_claim_cnsdr='no'
   then 
      case 
         when last_claim_idntfr=1 and (date_add(index_end_date,0) between date_add(claim_date_mod,0) and claim_end_date_w_dos)
         then lookforward_mod - datediff(date_add(index_end_date,0), date_add(claim_date_mod,0))
         when last_claim_idntfr=1 and (date_add(index_end_date,0) not between date_add(claim_date_mod,0) and claim_end_date_w_dos)
         then lookforward_mod - sum(case when last_claim_idntfr=1 then dos_drvd else 0 end) over (partition by {patient_gid_clmn},{product_name_clmn},ntb_rnk)
         else 0
      end 
end as time_range_f_dos

,case when (row_number() over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by episode_num_drvd,claim_date_mod))=1 then 1 else 0 end as roll_up_column


from
(
--** Define claim end date, NTB Filter criteria and flag claims where the index end cut through **--

select 
pat_in_lkfrwd.*
,cast(FROM_UNIXTIME(UNIX_TIMESTAMP(date_add(claim_date_mod,cast(dos_trim as int)),'yyyy-MM-dd'),'yyyy-MM-dd 00:00:00') as timestamp) as claim_end_date_w_trim_dos
,cast(FROM_UNIXTIME(UNIX_TIMESTAMP(date_add(index_date,cast(lookforward_mod as int)),'yyyy-MM-dd'),'yyyy-MM-dd 00:00:00') as timestamp) as index_end_date


from
(
--** Define the patient cohort and also trim lookforward if it ends beyond data end date **--

select input_prmtrs.*
,case 
   when cohort_grp='monthly' 
   then concat(month(index_date),'-',year(index_date))
   when cohort_grp='quarterly' 
   then concat((int((month(index_date)-1)/3)+1), '-', year(index_date))
   when cohort_grp='semesterly' 
   then concat((int((month(index_date)-1)/6)+1),'-', year(index_date))
   when cohort_grp='annually' 
   then year(index_date) 
   when cohort_grp='overall' 
   then 'overall'       
end as patient_cohort

,case 
   when date_add(index_date,cast(lookforward as int)) > data_end_date
   then cast(datediff(data_end_date,index_date) as int)
   else cast(lookforward as int)
end as lookforward_mod

,case 
   when ntb_rnk_fltr_typ='first'
   then min(ntb_rnk) over (partition by {patient_gid_clmn},{product_name_clmn})
   when ntb_rnk_fltr_typ='last'
   then max(ntb_rnk) over (partition by {patient_gid_clmn},{product_name_clmn})
   when ntb_rnk_fltr_typ='all'
   then ntb_rnk
   else ntb_rnk
end as ntb_rnk_fltr

from
(
--** Define the constraints (index_date,lookforward, data_end_date, cohort group, which ntb event to pick) on which compliance should be calculated **--
--** dos_trim is created to consider overlapping claim to end at next claim start **--
--** ntb_rnk_fltr_typ is created to select the required NTB Event (First, Last or All) **--

select src.*
,case 
   when next_claim_date_drvd <= claim_end_date_w_dos 
   then datediff(next_claim_date_drvd,{claim_start_dt_clmn}) 
   else dos_drvd
end as dos_trim

,{claim_start_dt_clmn} as claim_date_mod
,cast(FROM_UNIXTIME(UNIX_TIMESTAMP(min({index_dt}) over (partition by {patient_gid_clmn}, {product_name_clmn}, ntb_rnk order by {index_dt}),'yyyy-MM-dd'),'yyyy-MM-dd 00:00:00') as timestamp) as index_date 
,'{lookforward_vl}' as lookforward 
,'{last_claim_cnsdr_vl}' as last_claim_cnsdr
,'{ntb_rnk_fltr_typ_vl}' as ntb_rnk_fltr_typ
,'{cohort_grp_vl}' as cohort_grp
,cast(FROM_UNIXTIME(UNIX_TIMESTAMP(date_sub(add_months(concat(from_unixtime(unix_timestamp({data_end},'yyyy-MM-dd'), 'yyyy-MM'),'-01'),1),1),'yyyy-MM-dd'),'yyyy-MM-dd 00:00:00') as timestamp) as data_end_date

from
--** Source Data from User**-- 
{src_input_tbl} as src
)input_prmtrs
)pat_in_lkfrwd
where ntb_rnk_fltr=ntb_rnk
and lookforward>=lookforward_mod  
--and to_date(data_end_date)<=case when last_claim_cnsdr='yes' then to_date(episode_end_date1_drvd) when last_claim_cnsdr='no' then to_date(episode_end_date3_drvd) else to_date(data_end_date) end

)ntb_rnkng
)mtrcs
)metrics_rolled
)cmplnc
where roll_up_column=1
--group by  {roll_up_lvl_clmns},episode_num_drvd, ntb_rnk, dos_w_index_roll, time_range_roll, dos_w_index_roll_f_dos, time_range_roll_f_dos, cmplnc_dos_dot, cmplnc_dos_time_range, cmplnc_dot_time_range, cmplnc_dos_dot_f_dos, cmplnc_dos_time_range_f_dos, cmplnc_dot_time_range_f_dos, dos_w_index_roll_sngl, dot_w_index_roll_sngl, time_range_roll_sngl, dos_w_index_roll_sngl_f_dos, dot_w_index_roll_sngl_f_dos, time_range_roll_sngl_f_dos
)rqrd_lvl
group by {roll_up_lvl_clmns},ntb_rnk
'''.format(**kwargs))

    return compliance_module
