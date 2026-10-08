# ############################################## Module Information ####################################################
# Module              : stencil
# Classes             : init
# Purpose             : Contains stencil's caller function to make dictionary and parameter validation
# Consuming module    :
# Created on          : 20-12-2018
# Last changed on     : 03-02-2019
# Last changed by     : Kuldeep Singh chauhan
# Reason for change   : Integration of stencils
# ######################################################################################################################
# All imports:
import inspect
from common_utilities import df_generator_utility

###################################################################################################################

class init(object):
    def __init__(self, spark=None):
        if spark is None:
            print("Spark session object is not passed ")
        else:
            self.spark = spark

    #####################################################Source Of Business#############################################

    def sob(self, **kwargs):
        """USAGE : stencil.init(<SparkSession>).sob()
        ** Use below parameters as per instruction
        --> lookback- Provide integer value or specific lookback column from source
        --> grace- Provide integer value or specific grace column from source
        --> dedup_type_vl- Provide specific values from ["no", "yesadd", "yesremove"]
        --> dedup_partition_on_clmns- Provide the columns on which multiple claims of same product on single day should be deduped
        --> dedup_ranking_order_clmns- Provide the columns for ranking multiple claims of same product on single day
        --> dos_metric_partition_on_clmns- Provide the columns for rolling up DOS in case of DOS dedup
        --> dos_clmn- Provide integer value or specific Days of Supply column from source
        --> patient_gid_clmn- Provide required patient_gid column from source
        --> claim_id_clmn- Provide required claim_id column from source
        --> claim_start_dt_clmn- Provide required claim_date column from source
        --> product_name_clmn- Provide required Product column from source
        --> src_input_tbl- Provide the database-table name or select query (include select query in bracket)
        --> metric_ordering_by_following_clmns- Provide the order for calculating various next SOB metrics like next claim date, gap to next claim
        --> metric_ordering_by_clmns- Provide the order for calculating various previous SOB metrics like previous claim date, gap from previous claim
        --> required_grace- Provide integer value or required column from source to add grace to episode days if required
        --> data_end_required- Specify if data end date should be considered for Episode days calculation or not. Specific value ["yes","no"]
        """
        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df
    #####################################################Eligibility####################################################

    def eligibility(self, **kwargs):
        """USAGE : stencil.init(<SparkSession>).eligibility()
        ** Use below parameters as per instruction
        --> entity_input_tbl : User should specify the  input table on which eligibilty needs to be flagged(entity can be patient,physician and pharmacy)
        --> activity_input_tbl 	: User should specify the activity table of the entity on which eligibility flags needs to be mapped(can be patient activity, physician activity or pharmacy activity)
        --> index_date_clmn	: user should specify column to be used as reference for analysis window.
        --> lb_ll_vl :	User should specify the lower limit of lookback window.
        --> lb_ul_vl :	User should specify the upper limit of lookback window.
        --> lf_ll_vl :	User should specify the lower limit of lookforward  window.
        --> lf_ul_vl:	User should specify the upper limit of lookforward window.
        --> lb_th_vl:	User should specify the cutoff criteria for an entity to be active in lookback.
        --> lf_th_vl :	User should specify thecutoff criteria for an entity to be active in lookforward.
        --> frequency_vl :	User should specify the frequency at which eligibility flags have to be calculated.
        --> Grain_vl : User should specify the grain of the activity table from source.
        --> calendar_align_vl: User should specify the option whether the index date has to be aligned with the calender frequencies or not.
        --> sub_activity_type_vl :	User should specify the  filter to be applied on the type of activity to be considered for patient,physician and pharmacy
        --> join_id_clmn	: User should specify column on which entity input table and activity input table has to be joined.
        --> level_clmns :	User should specify columns which form the grain of the entity_input_tbl. The index_dt_clmn should be unique at the level_columns.

        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df
    #####################################################Episode########################################################

    def episode(self, **kwargs):
        """USAGE : stencil.init(<SparkSession>).episode()
        ** Use below parameters as per instruction
        --> patient_gid_clmn- Provide required patient_gid column from source
        --> src_input_tbl- Provide the database-table name or select query (include select query in bracket)
        --> product_name_clmn- Provide required Product column from source
        --> claim_rnkn_partition_on_clmns- Provide the partition columns to get 1st claim for the purpose of getting single grace, lookback and claim id for an episode
        --> claim_rnkn_ordering_by_clmns- Provide the ordering columns to get 1st claim for the purpose of getting single grace, lookback and claim id for an episode
        --> claim_id_clmn- Provide required claim_id column from source
        --> episode_end_dts_clmns- Provide the episode end date columns required to be shown in episode output. Specific columns to be picked from output of SOB.
        --> claim_start_dt_clmn- Provide required claim_date column from source
        --> drug_class_clmn- Provide the drug class column. Pass "NA" if not applicable for the franchise.
        --> dos_null_flag_clmns- Provide the Null DOS columns required to be shown in episode output. Specific columns to be picked from output of SOB.
        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df

    #####################################################Regimen########################################################

    def regimen(self, **kwargs):
        """USAGE : stencil.init(<SparkSession>).regimen()
        ** Use below parameters as per instruction
        --> patient_gid_clmn- Provide required patient_gid column from source
        --> src_input_tbl- Provide the database-table name or select query (include select query in bracket)
        --> product_name_clmn- Provide required Product column from source
        --> episode_end_dt_clmn- Specify the episode end date column on which the regimen should be calculated
        --> final_indication- Specify the final indication if applicable else pass "NA"
        --> episode_start_dt_clmn- Specify the episode start date column
        --> regimen_removal_vl- Specify value as 0 if only removed regimens are to be kept, 1 if removed regimens are to be removed and (0,1) if all regimens are to be kept
        --> regimen_threshold_vl- Specify the regimen threshold value in number of days
        --> clean_up_type_vl- Specify specific values whether clean up is required or not. ["no", "yes"]
        --> collect_type_rgmn_vl- Specify whether duplicates in the product regimen name should be stored or removed. Use collect_list if duplicates are to be kept otherwise use use collect_set to remove duplicates.
        --> collect_type_drg_rgmn_vl- Specify whether duplicates in the drug regimen name should be stored or removed. Use collect_list if duplicates are to be kept otherwise use use collect_set to remove duplicates.
        --> data_end_dt_vl- Specify the data end date in yyyy-MM-dd format
        --> drug_class_clmn- Specify drug class column source if applicable else pass "NA"
        --> regimen_replace_clmn- Specify the regimen column for which certain product/ drug names shoudl be changed to a specific value. Possible columns- regimen, drug_regimen
        --> product_replace_from_vls- Specify the list of values which are to be replaced
        --> product_replace_to_vls- Specify the value to which the list of values should be updated to
        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df

    ################################################patientSelection##################################################

    def patientSelection(self, **kwargs):
        """
        USAGE : stencil.init(<SparkSession>).patientSelection()
        ** Use below parameters as per instruction
        --> criteria_name  : User should provide names of criterias to be applied as elements of list.
        --> level_clmns : User should provide column/columns name to generate the output rolled up at these columns as elements of list.
        --> src_input_tbl : User should provide the table name directly with database name on which the stencil has to be run.
        --> index_dt : User should provide dates , on the basis of which analysis windpw needs to be created as elements of list.
        --> data_end_dt_vl : User should provide the data end date in format of 'YYYY-MM-DD'
        --> ll_vl : User should provide lower limit value on the basis of which analysis window will be created for all criterias as elements of list.
        --> ul_vl :  User should provide upper limit value on the basis of which analysis window will be created for all criterias as elements of list.
        --> filtered_clmn: User should specify the valid column on which filter has to be applied for each criteria as elements of list.
        --> filtered_vl: User should specify the filter values for each filtered column as elements of list.
        --> filtered_dt_clmn: User should specify any valid date column  which will be compared with analysis window for each criteria as elements of list.
        --> agg_func : user should specify the aggregation function to be applied for each criteria as elements of list.
        --> cutoff_criteria: user should provide the cut-off value for which an entity will pass the criteria test.
        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df

    ################################################episodePersistency################################################

    def episodePersistency(self, **kwargs):
        """
        USAGE : stencil.init(<SparkSession>).episodePersistency()
        ** Use below parameters as per instruction
        --> cohort_input_tbl : User should provide following manually maintained    table name, mabi_period_cohort_ref_tbl or any other table with similar structure.
        --> src_input_tbl : User should provide the table name directly with database name on which the stencil has to be run.
        --> index_dt_clmn : User should provide any date column, on the basis of which patient cohort needs to be created.
        --> data_end_dt_vl : User should provide the data end date in format of 'YYYY-MM-DD'
        --> lookforward_option_vl : User should provide any one value from LOV, on the basis of which patient pool will be created across period months
        --> persistency_period_vl : User should provide no of days for which persistency need to be tracked
        --> level_rollup_clmns : User should provide column/columns name to generate the output rolled up at these columns
        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df


    ################################################oneNdone###################################################

    def oneNdone(self, **kwargs):
        """
        USAGE : stencil.init(<SparkSession>).oneNdone()
        ** Use below parameters as per instruction
        --> src_input_tbl- User should provide the table name directly or select query of the SOB stencil output table
        --> lookforward_mnth- User should provide the number of months in which patient needs to be monitored to call it a one and done patient
        --> market_def_clmn- User should provide column name which contains product/product group/drug class name to define the market to call a patient one and done in that market
        --> level_rollup_clmns- User should provide column/columns name to generate the output rolled up at these columns
        --> sob_rank_vl- User should provide any one value LOV, on the basis of which patient initiation date need to be created
        --> ntb_ntm_filter_vl- User should provide any one value LOV, on the basis of which patient cohort needs to be created
        --> index_dt_clmn- User should provide any date value, on the basis of which patient cohort needs to be created
        --> patient_gid_clmn- User should provide the patient identifier column name
        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df

    ################################################compliance###################################################

    def compliance(self, **kwargs):
        """
        USAGE : stencil.init(<SparkSession>).compliance()
        ** Use below parameters as per instruction
        --> src_input_tbl- Provide the database-table name or select query (include select query in bracket)
        --> patient_gid_clmn- Provide required patient_gid column from source
        --> product_name_clmn- Provide required Product column from source
        --> claim_start_dt_clmn- Provide required claim_date column from source
        --> index_dt- Specify specific column from source or a pass a date in yyyy-MM-dd format
        --> lookforward_vl- Specify the lookforward period
        --> last_claim_cnsdr_vl- Specify if last claim should be considered or not. Choose from ["no", "yes"]
        --> ntb_rnk_fltr_typ_vl- Specify which NTB events should be picked for compliance calculations. Choose from specific_value": ["first", "last", "all"]
        --> cohort_grp_vl- Specify the cohort grouping level. Choose from specific value ["monthly", "quarterly", "semesterly", "annually", "overall"]
        --> data_end- Specify the data end date in yyyy-MM-dd format
        --> roll_up_lvl_clmns- Specify the final roll up columns for compliance
        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df

    #####################################################PatientPersistency############################################

    def patientPersistency(self, **kwargs):
        """
        USAGE : stencil.init(<SparkSession>).patientPersistency()
        ** Use below parameters as per instruction
        -->	src_input_tbl: User should provide the table name directly with database name or select query with following mandatory columns (any order) in following format:
        (SELECT Product_Name,patient_gid,grace,spike5_pharmacy_flag,spike5_pharmacy_date,episode_start_date_drvd,ntb_flag,episode_length,rnk from table)
        -->	cohort_input_tbl: User should provide following manually maintained table name, mabi_period_cohort_ref_tbl or any other table with similar structure
        -->	index_dt_clmn: User should provide any date column, on the basis of which patient cohort needs to be created
        -->	ntb_ntm_filter_vl: User should provide any one value from LOV, on the basis of which patient cohort needs to be created
        -->	lookforward_option_vl: User should provide any one value from LOV, on the basis of which patient pool will be created across period months
        -->	persistency_period_vl: User should provide no of days for which persistency need to be tracked and should be divisible by 30
        -->	level_rollup_clmns: User should provide column/columns name to generate theoutput rolled up at these columns
        -->	cohort_grp_vl: User should provide any one value from LOV, on the basis of which patient cohort will be created to track persistency
        -->	num_ontherapy_threshold_vl: User should provide threshold value in days, to check minimum episode overlap between period start date and period end date and flag persistent patient as 1 or 0
        -->	data_end_dt_vl: User should provide the data end date in format of '"YYYY-MM-DD"'
        -->	method_vl: User should provide method number as per which persistency need to be calculated
        -->	sob_rank_vl: User should provide any one value from LOV, on the basis of which patient pool will be created across period months
        -->	include_grace_vl: User should provide 'Yes' in case grace need to be considered for persistency calculation
        -->	denum_ontherapy_threshold_vl: User should provide threshold value in days, to check minimum episode overlap between period start date and period end date and flag patient as 1 or 0

        """

        df = df_generator_utility.df_generator(self.spark, **kwargs)
        return df
