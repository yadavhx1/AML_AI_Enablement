# coding=utf-8
# ############################################## Module Information ####################################################
# Module              : businessLogic_sob
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# ######################################################################################################################


def business_logic(spark, **kwargs):
    sob_parameter_pass_check_v1 = spark.sql('''
--------------------------------------------------
--Module Name :-   MABI_PLD_SOB_TBL
--Module description : - This module will create Source Of Business and some Episode details for patients 
--Parameters required :- Databasename, Tablename, Lookback, Grace, Partition, Order
--Created by :- ABHISAX
--Created on :- 15 Nov 2018
--Version History :- N/A
---------------------------------------------------

--** Creating additional Episode columns and Therapy details **--
--Detail for End_Date2-> episode_end_date1_drvd with grace of last claim added to it
--Detail for dos_wo_last_claim-> Calculates the sum of DOS for the claims within an episode, by rejecting the last claim. In case of single claim, the value is 0
-- Detail for dos_last_claim-> Identifies the last claim's DOS within an episode
-- Detail for dos_wo_last_claim_no_overlap-> Calculates the sum of DOS within an episode, in case next claim overlaps current claim then next claim date - current claim is considered as DOS. Last claim is rejected for the calculation. In case of single claim the value is 0.

select 
sob_dtls.*
,cast(date_add(episode_end_date1_drvd,cast(first_value(grace_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by temp_row_num desc) as int)) as timestamp) as episode_end_date2_drvd 

,cast(date_add(min({claim_start_dt_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd),cast(episode_length as int)) as timestamp) as episode_end_date4_drvd 

,first_value(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by temp_row_num desc) as dos_last_claim

,case when count({claim_id_clmn}) over(partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)=1 then 0 else sum(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)- first_value(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by temp_row_num desc) end as dos_wo_last_claim

,case when count({claim_id_clmn}) over(partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)=1 then 0 else sum(case when next_claim_date_drvd< claim_end_date_w_dos then datediff(next_claim_date_drvd,{claim_start_dt_clmn}) else dos_drvd end) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)- first_value(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by temp_row_num desc) end as dos_wo_last_claim_no_overlap

,datediff({claim_start_dt_clmn},prev_any_claim_date_drvd) as gap_frm_prev_any_clm_strt_drvd

,case when dos_drvd is null then 1 else 0 end as dos_null_flag

,case when sum(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn}) is null then 1 else 0 end as dos_pat_prd_null_flag

,case when sum(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) is null then 1 else 0 end as dos_pat_prd_epsd_null_flag

from

(
--** Creating Episode columns and NTB flags **--

--Detail for episode_end_date1_drvd-> Last Claim's Start Date + Last Claim's DOS for the episode
--Detail for episode_end_date3_drvd-> Last claim's start date within the episode. In case of single claim, this value is Null
--Detail for last_claim_idntfr-> Last claim of the Episode is marked as 1, all others as 0
select episode_dtls.*
,first_value(sob_lvl7) over (partition by {patient_gid_clmn},{product_name_clmn},ntb_rnk order by NTB_Flag_Rank) as NTB_FLAG

,min({claim_start_dt_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as episode_start_date_drvd

,cast(date_add(max({claim_start_dt_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd),cast(first_value(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by temp_row_num desc) as int)) as timestamp) as episode_end_date1_drvd 

,case when count({claim_id_clmn}) over(partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd)=1 then null else max({claim_start_dt_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) end as episode_end_date3_drvd

,sum(episode_days) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as episode_length

,sum(episode_days_overlap) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) as episode_length_overlap

,case when temp_row_num=max(temp_row_num) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd) then 1 else 0 end as last_claim_idntfr

from
(
--**Creating NTB Ranks and row number for dos columns**--

-- Detail for ntb_rnk-> Populate the NTBs rank to all successive Non NTB SOBs until there is a change in NTB SOB
-- Detail for NTB_Flag_Rank-> Assign row numbers to the claims which would be later used to populate NTB SOBs to subsequent Non NTB SOBs
--Detail for temp_row_num-> Ranking the claims within a episode to later used for identifying last claim within an Episode

select ntb_rnkng.*

,max(ntb_tmp_rnk) over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns} rows unbounded preceding) as ntb_rnk 

,row_number() over (partition by {patient_gid_clmn},{product_name_clmn},max(ntb_tmp_rnk) over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns} rows unbounded preceding) order by {metric_ordering_by_clmns}) as NTB_Flag_Rank

,cast(row_number() over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by {metric_ordering_by_clmns}) as int) as temp_row_num 

,case 
               when date_add(next_claim_date_drvd,0)<= date_add(claim_end_date_w_dos,0)
               then dos_drvd 
               else episode_days 
               end as episode_days_overlap

from 
(
--** Getting 4 and 2 level SOBs from level 7 SOB **--
-- Detail for ntb_tmp_rnk-> Assign successive ranks to the NTBs and 0 for all non NTB SOBs.

select sob_rollup.*
,
case 
               when sob_lvl7='NTB NAIVE' then 'NTB' 
               when (sob_lvl7='NTB ADDON' or sob_lvl7='NTB SWITCH' or sob_lvl7='RS ADDON' or sob_lvl7='RS SWITCH') then 'SWITCH'
               when sob_lvl7='RS SAME' then 'REINITIATING'
               when sob_lvl7='C' then 'C'
               else sob_lvl7
end as sob_lvl4
,case 
               when (sob_lvl7='NTB NAIVE' or sob_lvl7='NTB ADDON' or sob_lvl7='NTB SWITCH' or sob_lvl7='RS ADDON' or sob_lvl7='RS SWITCH') then 'INFLOW' 
               when (sob_lvl7='RS SAME' or sob_lvl7='C') then 'NON INFLOW'
               else sob_lvl7
end as sob_lvl2_1
,
case 
               when (sob_lvl7='NTB NAIVE' or sob_lvl7='NTB ADDON' or sob_lvl7='NTB SWITCH' or sob_lvl7='RS ADDON' or sob_lvl7='RS SWITCH') then 'NEW' 
               when (sob_lvl7='RS SAME' or sob_lvl7='C') then 'C/REINITIATING'
               else sob_lvl7
end as sob_lvl2_2

,case when sob_lvl7 like 'NTB%' then dense_rank() over (partition by {patient_gid_clmn},{product_name_clmn},sob_lvl7 like 'NTB%' order by {metric_ordering_by_clmns}) else 0 end as ntb_tmp_rnk
,sum(is_episode_start)  over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns} rows unbounded preceding) as episode_num_drvd
from
(
--** Calculating 7 level SOB for finite and infinite SOB **--

select sob_7_lvl.*
,case 
               when cast(is_episode_start as int)=1 and lookback_drvd='infinite' 
               then 
               case when inf_pat_rank=1 
                                              then 'NTB NAIVE'

                                             when prev_final_product_name_drvd={product_name_clmn}
                                             then 'RS SAME'

                                             when (max(is_episode_end) over (partition by {patient_gid_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding)=1) and (date_add(prev_any_claim_date_drvd,cast(prev_any_product_dos_drvd as int))) < date_add(claim_end_date_w_dos,0) --[uk] make edits here
                                                            then 
                                                                           case when inf_pat_prod_rank=1
                                                                                          then 'NTB SWITCH'
                                                                                          else 'RS SWITCH'
                                                                           end
                                                            else 
                                                                           case when inf_pat_prod_rank=1
                                                                                          then 'NTB ADDON'
                                                                                          else 'RS ADDON'
                                                                           end
               end
                              else 
                              case when cast(is_episode_start as int)=0 and lookback_drvd='infinite'
                              then 'C' 

else 
               case when cast(is_episode_start as int)=1 and lookback_drvd<>'infinite'
                              then
                                             case when prev_any_claim_date_drvd is null 
                                                            then 'NTB NAIVE'

                                                            when  (datediff({claim_start_dt_clmn},date_add(prev_any_claim_date_drvd,cast(prev_any_product_dos_drvd as int))))>max(lookback_drvd) over(partition by {patient_gid_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding)
                                                            then 'NTB NAIVE'

                                                            when prev_final_product_name_drvd={product_name_clmn}
                                                            then 'RS SAME'

                                                            when (max(is_episode_end) over (partition by {patient_gid_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding)=1) and (date_add(prev_any_claim_date_drvd,cast(prev_any_product_dos_drvd as int))) < date_add(claim_end_date_w_dos,0) --[uk] make edits here 
                                                            then 
                                                                           case when prev_claim_date_drvd is null or datediff({claim_start_dt_clmn},(date_add(prev_claim_date_drvd,cast(prev_product_dos_drvd as int))))>lookback_drvd --[uk] make edits here
                                                                                          then 'NTB SWITCH'
                                                                                          else 'RS SWITCH'
                                                                           end 
                                                            else 
                                                                           case when prev_claim_date_drvd is null or datediff({claim_start_dt_clmn},(date_add(prev_claim_date_drvd,cast(prev_product_dos_drvd as int))))>lookback_drvd --[uk] make edits here
                                                                                          then 'NTB ADDON'
                                                                                          else 'RS ADDON'
                                                                           end 
                                             end 
                                                            else
                                                            case when cast(is_episode_start as int)=0 and lookback_drvd<>'infinite'
                                                            then 'C' 
                                                            end 
                              end 
               end 
end as sob_lvl7

from
(
--** Calculating Episode metrics required to derive SOB **--

select episode_metrics.*
,case when prev_claim_date_drvd is null 
                 then 1 
                 when gap_from_prev_claim_drvd > max(cast(grace_drvd as int)) over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding) 
                 then 1 
                 else 0 
end as is_episode_start

,case 
               when gap_to_next_claim_drvd > cast(grace_drvd as int) or next_claim_date_drvd is null 
               then 1 
               else 0 
end as is_episode_end 

from
(
--** Calculating additional metrics required for SOB. Calculating episode days. **--
--Detail for parameter {required_grace}- By default {required_grace} is 0. This can be 0 or grace_drvd column.

select 
sob_metrics_2.*
,datediff({claim_start_dt_clmn},(date_add(prev_claim_date_drvd,cast(prev_product_dos_drvd as int)))) as gap_from_prev_claim_drvd 
,datediff(next_claim_date_drvd,claim_end_date_w_dos) as gap_to_next_claim_drvd
--,case when date_add(next_claim_date_drvd,0) <= date_add(claim_end_date_w_dos, cast(grace_drvd as int)) then datediff(next_claim_date_drvd,{claim_start_dt_clmn}) else dos_drvd + {required_grace} end as episode_days --[uk] make edits here

,case 
               when data_end_rqrd='yes' 
               then 
                              case 
                                             when date_add(next_claim_date_drvd,0) <= date_add(claim_end_date_w_dos, cast(grace_drvd as int)) 
                                             then datediff(next_claim_date_drvd,{claim_start_dt_clmn}) 
                                             when next_claim_date_drvd is null 
                                             then 
                                                            case 
                                                                           when date_add(claim_end_date_w_dos, cast(grace_drvd as int)) <= last_day(concat(substr(max(data_period) over (partition by null),1,4),'-',substr(max(data_period) over (partition by null),5,6),'-01'))
                                                                           then dos_drvd
                                                                           else dos_drvd + cast(grace_drvd as int)
                                                            end
                                             else dos_drvd
                              end
               when data_end_rqrd='no'
               then 
                              case 
                                             when date_add(next_claim_date_drvd,0) <= date_add(claim_end_date_w_dos, cast(grace_drvd as int)) 
                                             then datediff(next_claim_date_drvd,{claim_start_dt_clmn}) 
                                             else dos_drvd + {required_grace} 
                              end
               else null
end as episode_days



from
(
--** Calculating various dates, product and rank metrics required to derive SOB **--
--Detail for inf_pat_rank-> Identifies the 1st claim for the patient. This is required for creating infinite SOB.
--Detail for inf_pat_prod_rank-> Identifies the 1st claim for the patient- product. This is required for creating infinite SOB.

select sob_metrics.*
,cast(date_add({claim_start_dt_clmn},cast(dos_drvd as int)) as timestamp) as claim_end_date_w_dos 
,row_number() over (partition by {patient_gid_clmn} order by {metric_ordering_by_clmns}) as inf_pat_rank

,row_number() over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns}) as inf_pat_prod_rank

,max({product_name_clmn}) over (partition by {patient_gid_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding) as prev_final_product_name_drvd 

,max({claim_start_dt_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding) as prev_claim_date_drvd

,max({claim_start_dt_clmn}) over (partition by {patient_gid_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding) as prev_any_claim_date_drvd

,max(dos_drvd) over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding) as prev_product_dos_drvd

,max(dos_drvd) over (partition by {patient_gid_clmn} order by {metric_ordering_by_clmns} rows between 1 preceding and 1 preceding) as prev_any_product_dos_drvd

,max({claim_start_dt_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn} order by {metric_ordering_by_following_clmns} rows between 1 following and 1 following) as next_claim_date_drvd

,max({claim_start_dt_clmn}) over (partition by {patient_gid_clmn} order by {metric_ordering_by_following_clmns} rows between 1 following and 1 following) as next_any_claim_date_drvd 

from
(
select src_dedup.* from 
(
--**Creating dedup flag and defining new dos in case of deduping**--
-- Detail for Dedup_Flag-> This flag helps in identifying the relevant rows to be considered from the set of claims falling single day for the same patient- product
-- Detail for dos_drvd-> Updated DOS in case of multiple claims on single day for same patient- product

select src_dedup_flag.*
,case when dedup_type like 'yes%' and rnk>1 then 1 else 0 end as dedup_flag
,case when dedup_type='yesadd'
then sum({dos_clmn}) over(partition by {dos_metric_partition_on_clmns}) else {dos_clmn} end as dos_drvd

from
(
--**Creating rank for deduping**--
--Detail for Rnk-> Creating Rank for deduping productâ€™s multiple claims on single day (Can have same DOS, therefore we further break the tie by using claim_date, claim_id and other entity if required)

select 
src_dedup_rnk.*
,row_number() over(partition by {dedup_partition_on_clmns} order by {dedup_ranking_order_clmns}) as rnk 

from
(
--** Fetching input data for SOB and defining lookback, grace and dedup type **--
--dedup_type is parameterized with fixed value as-> no, yesadd, yesremove

select src.*
,{lookback} as lookback_drvd   
,{grace} as grace_drvd 
,'{dedup_type_vl}' as dedup_type 
,'{data_end_required}' as data_end_rqrd
from 
--The select clause is parameterized to account for any column addition or modification. Select clause should be closed within braces, database and tablename should not be enclosed
{src_input_tbl} src
)src_dedup_rnk
)src_dedup_flag
)src_dedup
where dedup_flag='0'
)sob_metrics
)sob_metrics_2
)episode_metrics
)sob_7_lvl
)sob_rollup
)ntb_rnkng
)episode_dtls
)sob_dtls
    '''.format(**kwargs
               )
                                            )
    return sob_parameter_pass_check_v1