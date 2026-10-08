# coding=utf-8
# ############################################## Module Information ####################################################
# Module              : businessLogic_oneNdone
# Classes             : N.A.
# Purpose             : Runs SQL query
# Consuming module    : stencil
# Created on          : 25-01-2019
# Last changed on     :
# Last changed by     : Kuldeep Singh chauhan
# Reason for change   : OneNdone integration
# ######################################################################################################################

def business_logic(spark, **kwargs):
    oneNdone_query_string = ('''
select {level_rollup_clmns}, 
    sum(oneNdone) as oneNdone,
    sum(twoNdone) as twoNdone,
    sum(threeNdone) as threeNdone,
    sum(fourNdone) as fourNdone,
    sum(fiveNdone) as fiveNdone,
    sum(sixNdone) as sixNdone,
    sum(sevenNdone) as sevenNdone,
    sum(eightNdone) as eightNdone,
    sum(nineNdone) as nineNdone,
    sum(tenNdone) as tenNdone,
    sum(elevenNdone) as elevenNdone,
    sum(twelveNdone) as twelveNdone,
    sum(claim_count_col) as nNdone,
    count(distinct patient_gid) as no_incident_patient

from(
	select src_market_claim_flag.*,   
		case when claim_count_col=1  then 1 else 0 end as oneNdone,  
		case when claim_count_col=2  then 1 else 0 end as twoNdone,
		case when claim_count_col=3  then 1 else 0 end as threeNdone,
		case when claim_count_col=4  then 1 else 0 end as fourNdone,
		case when claim_count_col=5  then 1 else 0 end as fiveNdone,
		case when claim_count_col=6  then 1 else 0 end as sixNdone,
		case when claim_count_col=7  then 1 else 0 end as sevenNdone,
		case when claim_count_col=8  then 1 else 0 end as eightNdone,
		case when claim_count_col=9  then 1 else 0 end as nineNdone,
		case when claim_count_col=10 then 1 else 0 end as tenNdone,  
		case when claim_count_col=11 then 1 else 0 end as elevenNdone,                              
		case when claim_count_col=12 then 1 else 0 end as twelveNdone
             
	from
	(
		select src_market_claim_count.*, sum(claim_flag) over 
		(partition by {patient_gid_clmn},{market_def_clmn},filtered_rank) as claim_count_col 
		from
		(
			select src_market.*,
			case 
				when date_add({index_dt_clmn},0) 
				between 
				date_add(min_index_date,0) 
                and 
                --date_add(add_months(CAST(DATE_ADD(min_index_date,1-DAY(min_index_date)) AS TIMESTAMP),{lookforward_days}),0) 
                date_add(min_index_date,{lookforward_days})
                then 1 else 0 end as claim_flag 
				,CAST(DATE_ADD(min_index_date,1-DAY(min_index_date)) AS TIMESTAMP) AS index_mon_start_date 
			from
			(
				select src.*,
				min({index_dt_clmn}) over( partition by  {patient_gid_clmn},{market_def_clmn},filtered_rank) 
				as min_index_date 
				from				
				(
				select inpt.*,
				case 
	            when upper(ntb_rnk_fltr_typ)='FIRST'
	            then min(ntb_rnk) over (partition by {patient_gid_clmn},{market_def_clmn})
	            when upper(ntb_rnk_fltr_typ)='LAST'
	            then max(ntb_rnk) over (partition by {patient_gid_clmn},{market_def_clmn})
	            when upper(ntb_rnk_fltr_typ)='ALL'
	            then ntb_rnk
	            else ntb_rnk
                end as filtered_rank
                from
                (
                select inp.*, upper('{sob_rank_vl}') as ntb_rnk_fltr_typ
				from {src_input_tbl} as inp 
				where upper(ntb_flag) like upper	('%{ntb_ntm_filter_vl}%') 
				)inpt
				)src
				where filtered_rank=ntb_rnk
			)src_market
		)src_market_claim_count

	)src_market_claim_flag 
)src_market_to_be_rolled_up
group by {level_rollup_clmns}
    '''.format(**kwargs
               ))

    oneNdone_df = spark.sql(oneNdone_query_string)

    return oneNdone_df