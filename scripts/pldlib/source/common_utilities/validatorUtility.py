# ############################################## Module Information ####################################################
# Module              : validatorUtility
# Classes             : N.A.
# Purpose             : contains utility that calls ruleGenerator on the specified parameters
# Consuming module    : stencil
# Created on          : 20-12-2018
# Last changed on     : 03-02-2019
# Last changed by     : Kuldeep Singh chauhan
# Reason for change   : Integration
# ######################################################################################################################
from common_utilities import dataChecks


def valid_stencil_arg_gen(rule_dict, function_name, **dict_in):
    valid_stencil_args = {}
    if len(dict_in) > 0:
        for key_in, val_in in dict_in.items():
            for key_src in rule_dict[function_name].keys():
                if key_in == key_src:
                    valid_stencil_args.update({key_in: val_in})
                else:
                    pass
    else:
        msg = "Error: No parameter provided please refer the stencil help, \n" \
              " following keys should be provided {0}".format(list(rule_dict[function_name].keys()))
        raise Exception(msg)
    return valid_stencil_args
########################################################################################################################


def diff_key_extractor(superset_dict,function_name, subset_dict):
    superset_dict_copy = superset_dict[function_name].copy()
    all(map(superset_dict_copy.pop, subset_dict))
    diff_keys = (list(superset_dict_copy.keys()))

    if len(diff_keys) > 0:
        msg = "Error: Following additional keys were expected as parameter but not provided: {0}". \
            format(diff_keys)
        raise Exception(msg)
    else:
        pass
    return None

########################################################################################################################


def validate_value(rule_dict, function_name, key, value):
    for k1, v1 in rule_dict[function_name][key].items():
        if isinstance(value, list):
            status = eval(
                "dataChecks.{k1}".format(k1=k1) + "('{key}',{value},{v1})".format(key=key, value=value, v1=v1))
            if status is True:
                return True
            else:
                return False
        else:
            status = eval(
                "dataChecks.{k1}".format(k1=k1) + "('{key}','{value}',{v1})".format(key=key, value=value, v1=v1))
            if status is True:
                return True
            else:
                return False

########################################################################################################################
