# ############################################## Module Information ####################################################
# Module              : businessLogic_episode
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          :
# Last changed on     :
# Last changed by     :
# Reason for change   :
# ######################################################################################################################


def business_logic(spark, **kwargs):
    episode_parameter_pass_check_v1 = spark.sql(''' 
--------------------------------------------------
--Module Name :-   MABI_PLD_EPISODE_TBL
--Module description : - This module will create Episode details for the patient 
--Parameters required :- Databasename, Tablename, Episode End Date
--Created by :- ABHISAX
--Created on :- 30 Nov 2018
--Version History :- N/A
---------------------------------------------------

select {patient_gid_clmn},{product_name_clmn},drug_class_epsd,ntb_rnk,ntb_flag,episode_num_drvd,episode_start_date_drvd,{episode_end_dts_clmns},episode_length,episode_length_overlap,episode_first_sob,dos_wo_last_claim,dos_wo_last_claim_no_overlap,dos_last_claim,{dos_null_flag_clmns},first_claim_id_drvd,last_claims_grace_drvd,last_claims_lookback_drvd

from
(
select {patient_gid_clmn},{product_name_clmn},drug_class_epsd,grace_drvd,lookback_drvd,ntb_rnk,ntb_flag,episode_num_drvd,episode_start_date_drvd,{episode_end_dts_clmns},episode_length,episode_length_overlap,dos_wo_last_claim,dos_wo_last_claim_no_overlap,dos_last_claim,{dos_null_flag_clmns}
,first_value({claim_id_clmn}) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by clm_rnk) as first_claim_id_drvd

,first_value(sob_lvl7) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by clm_rnk) as episode_first_sob

,first_value(grace_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by clm_rnk desc) as last_claims_grace_drvd

,first_value(lookback_drvd) over (partition by {patient_gid_clmn},{product_name_clmn},episode_num_drvd order by clm_rnk desc) as last_claims_lookback_drvd

from
(
select {patient_gid_clmn},{product_name_clmn},drug_class_epsd,{claim_start_dt_clmn},{claim_id_clmn},grace_drvd,lookback_drvd,sob_lvl7,ntb_rnk,ntb_flag,episode_num_drvd,episode_start_date_drvd,{episode_end_dts_clmns},episode_length,episode_length_overlap,dos_wo_last_claim,dos_wo_last_claim_no_overlap,dos_last_claim,{dos_null_flag_clmns}
,row_number() over (partition by {claim_rnkn_partition_on_clmns} order by {claim_rnkn_ordering_by_clmns}) as clm_rnk
from      
(
select {patient_gid_clmn},{product_name_clmn},{drug_class_clmn} as drug_class_epsd,{claim_start_dt_clmn},{claim_id_clmn},grace_drvd,lookback_drvd,sob_lvl7,ntb_rnk,ntb_flag,episode_num_drvd,episode_start_date_drvd,{episode_end_dts_clmns},episode_length,episode_length_overlap,dos_wo_last_claim,dos_wo_last_claim_no_overlap,dos_last_claim,{dos_null_flag_clmns}
from {src_input_tbl} as src
)bse
)sob_claim_rnkn
)epsd_dtls
group by {patient_gid_clmn},{product_name_clmn},drug_class_epsd,ntb_rnk,ntb_flag,episode_num_drvd,episode_start_date_drvd,

{episode_end_dts_clmns},episode_length,episode_length_overlap,episode_first_sob,dos_wo_last_claim,dos_wo_last_claim_no_overlap,dos_last_claim,{dos_null_flag_clmns},first_claim_id_drvd,last_claims_grace_drvd,last_claims_lookback_drvd
order by {patient_gid_clmn},episode_start_date_drvd,{product_name_clmn},episode_num_drvd'''.format(**kwargs))

    return episode_parameter_pass_check_v1

