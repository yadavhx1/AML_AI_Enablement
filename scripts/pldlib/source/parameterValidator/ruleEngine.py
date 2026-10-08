# ############################################## Module Information ####################################################
# Module              : ruleEngine
# Classes             : N.A.
# Purpose             : A dictionary that contains checks to be applied on parameters
# Consuming module    : stencil
# Created on          : 20-12-2018
# Last changed on     : 03-02-2019
# Last changed by     : Kuldeep Singh Chauhan
# Reason for change   : Integration
# ######################################################################################################################
ruleEngine = {
    "sob": {
        "lookback": {
            "nullable": False
        },
        "grace": {
            "nullable": False
        },
        "dedup_type_vl": {
            "specific_value":
            ["no", "yesadd", "yesremove"]
        },
        "dedup_partition_on_clmns": {
            "string_flag": True
        },
        'dedup_ranking_order_clmns': {
            "string_flag": True
        },
        "dos_clmn": {
            "string_flag": True
        },
        "patient_gid_clmn": {
            "string_flag": True
        },
        "claim_id_clmn": {
            "string_flag": True
        },
        "claim_start_dt_clmn": {
            "string_flag": True
        },
        "product_name_clmn": {
            "string_flag": True
        },
        "src_input_tbl": {
            "string_flag": True
        },
        "metric_ordering_by_following_clmns": {
            "string_flag": True
        },
        "dos_metric_partition_on_clmns": {
            "string_flag": True
        },
        "metric_ordering_by_clmns": {
            "string_flag": True
        },
        "required_grace": {
            "nullable": False
        }

    },
    "eligibility":
        { "index_dt_clmn": {
                "string_flag": True
            },
            "entity_input_tbl": {
                "string_flag": True
            },
            "activity_input_tbl": {
                "string_flag": True
            },
            "lb_ll_vl": {
                "integer_flag": True
            },
            "lb_ul_vl": {
                "integer_flag": True
            },
            "lf_ll_vl": {
                "integer_flag": True,
            },
            "lf_ul_vl": {
                "integer_flag": True
            },
            "lb_th_vl": {
                "integer_flag": True
            },
            "lf_th_vl": {
                "integer_flag": True
            },
            "frequency_vl": {
                "specific_value": ["monthly", "quarterly", "semesterly", "yearly"]
            },
            "calendar_align_vl": {
                "specific_value": ["no", "yes"]
            },
            "sub_activity_type_vl": {
                "specific_value": ["a", "r", "mail order / specialty", "others", "retail", "rx", "hx", "mx"]
            },
            "level_clmns": {
                "string_flag": True
            },
            "join_id_clmn": {
                "string_flag": True
            }
        },
    "episode":
        {
            "patient_gid_clmn": {
                "string_flag": True
            },
            "src_input_tbl": {
                "string_flag": True
            },
            "product_name_clmn": {
                "string_flag": True
            },
            "metric_ordering_by_clmns": {
                "string_flag": True
            },
            "claim_rnkn_partition_on_clmns": {
                "string_flag": True
            },
            "claim_rnkn_ordering_by_clmns": {
                "string_flag": True
            },
            "claim_id_clmn": {
                "string_flag": True
            },
            "episode_end_dts_clmns": {
                "string_flag": True
            },
            "claim_start_dt_clmn": {
                "string_flag": True
            },
            "drug_class_clmn": {
                "string_flag": True
            },
            "dos_null_flag_clmns": {
                "string_flag": True
            }

        },
    "regimen":
        {
            "patient_gid_clmn": {
                "string_flag": True
            },
            "src_input_tbl": {
                "string_flag": True
            },
            "product_name_clmn": {
                "string_flag": True
            },
            "episode_end_dt_clmn": {
                "string_flag": True
            },
            "final_indication": {
                "string_flag": True
            },
            "episode_start_dt_clmn": {
                "string_flag": True
            },
            "regimen_removal_vl": {
                "string_flag": True
            },
            "regimen_threshold_vl": {
                "integer_flag": True
            },
            "clean_up_type_vl": {
                "specific_value": ["no", "yes"]
            },
            "collect_type_rgmn_vl": {
                "specific_value": ["collect_list", "collect_set"]
            },
            "collect_type_drg_rgmn_vl": {
                "specific_value": ["collect_list", "collect_set"]
            },
            "data_end_dt_vl": {
                "string_flag": True
            },
            "drug_class_clmn": {
                "string_flag": True
            },
            "regimen_replace_clmn": {
                "string_flag": True
            },
            "product_replace_from_vls": {
                "string_flag": True
            },
            "product_replace_to_vls": {
                "string_flag": True
            }
        },
    "patientSelection":
        {
            "criteria_name": {
                "list_empty_flag": True
            },
            "index_date": {
                "list_empty_flag": True
            },
            "period_start": {
                "list_empty_flag": True
            },
            "period_end": {
                "list_empty_flag": True
            },
            "cutoff_criteria": {
                "list_empty_flag": True
            },
            "level_column": {
                "list_empty_flag": True
            },
            "date_cmp_clm": {
                "list_empty_flag": True
            },
            "filters": {
                "list_empty_flag": True
            },
            "agg_func": {
                "list_empty_flag": True
            }
        },
    "episodePersistency":
        {
            "src_input_tbl ": {
                "string_flag": True
            },
            "cohort_input_tbl ": {
                "string_flag": True
            },
            "cohort_grp_vl": {
                "specific_value": ["monthly", "quarterly", "semesterly", "yearly", "overall"]
            },
            "index_dt_clmn": {
                "string_flag": True
            },
            "data_end_date_vl": {
                "string_flag": True
            },
            "lookforward_option_vl": {
                "specific_value": ["fixed", "dynamic"]
            },
            "persistency_period_vl": {
                "integer_flag": True
            },
            "level_rollup_clmns ": {
                "string_flag": True
            }

        },
	"patientPersistency":
        {
		    "src_input_tbl": {
            "string_flag": True
            },
            "cohort_input_tbl": {
                "string_flag": True
            },
            "index_dt_clmn": {
                "string_flag": True
            },
            "ntb_ntm_filter_vl": {
                "specific_value": {"ntb naive", "ntb"}
            },
            "lookforward_option_vl": {
                "specific_value": ["fixed", "dynamic"]
            },
            "persistency_period_vl": {
                "integer_flag": True

            },
            "level_rollup_clmns": {
                 "string_flag": True
            },
            "cohort_grp_vl": {
                "specific_value": ["monthly","quarterly","semesterly","annually" "overall"]
            },
            "num_ontherapy_threshold_vl": {
                "integer_flag": True,
                "range_flag": [0, 30]
            },
            "data_end_dt_vl": {
                "string_flag": True
            },
            "method_vl": {
                "integer_flag": True,
                "range_flag": [2, 5]
            },
            "sob_rank_vl": {
                 "specific_value": ["first","last","all"]
            },
            "include_grace_vl": {
                "specific_value": ["yes", "no"]
            },
            "denum_ontherapy_threshold_vl": {
                "integer_flag": True,
                "range_flag": [0, 30]
            }
        },
"oneNdone": {
         "src_input_tbl": {
            "string_flag": True
        },
        "lookforward_mnth": {
            "integer_flag": True
        },
        "market_def_clmn": {
            "string_flag": True
        },
        "level_rollup_clmns": {
            "string_flag": True
        },
        "sob_rank_vl": {
                 "specific_value": ["first","last","all"]
        },
        "ntb_ntm_filter_vl": {
                 "specific_value": ["ntb naive","ntb"]
        },
       "index_dt_clmn": {
            "string_flag": True
        },
        "patient_gid_clmn": {
            "string_flag": True
        }

    },
"compliance": {
        "src_input_tbl": {
            "string_flag": True
        },
        "patient_gid_clmn": {
            "string_flag": True
        },
        "product_name_clmn": {
            "string_flag": True
        },
        "claim_start_dt_clmn": {
            "string_flag": True
        },
        "index_dt": {
            "nullable": False
        },
        "lookforward_vl": {
            "integer_flag": True
        },
        "last_claim_cnsdr_vl": {
            "specific_value": ["no", "yes"]
        },
        "ntb_rnk_fltr_typ_vl": {
            "specific_value": ["first", "last", "all"]
        },
        "cohort_grp_vl": {
            "specific_value": ["monthly", "quarterly", "semesterly", "annually", "overall"]
        },
        "data_end": {
            "nullable": False
        },
        "roll_up_lvl_clmns": {
            "string_flag": True
        }
    }

}
