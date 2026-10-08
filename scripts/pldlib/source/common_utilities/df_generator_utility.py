# ############################################## Module Information ####################################################
# Module              : df_generator_utility
# Classes             : init
# Purpose             : A common utility to perform all validations and generate a dataframe
# Consuming module    : stencil
# Created on          : 03-02-2019
# Last changed on     : 03-02-2019
# Last changed by     : Kuldeep Singh chauhan
# Reason for change   : Integration of stencils
# ######################################################################################################################
# All imports:
# All the below imports are required for this module please don't delete them

from businessLogic import businessLogic_sob,\
     businessLogic_eligibility,\
     businessLogic_episode, \
     businessLogic_patientSelection, \
     businessLogic_regimen, \
     businessLogic_episodePersistency, \
     businessLogic_patientPersistency, \
     businessLogic_oneNdone, \
     businessLogic_compliance

########################################################################################################################
from common_utilities import validatorUtility, ruleEngine
import sys


def df_generator(spark, **kwargs):

    current_func_name = lambda n=0: sys._getframe(n + 1).f_code.co_name
    parent_func_name = current_func_name(1)
    try:
        stencil_args = validatorUtility.valid_stencil_arg_gen(ruleEngine.ruleEngine, parent_func_name, **kwargs)
    except Exception as e:
        msg = "Error: While creating valid stencil args, Following error occurred: {0} ".format(str(e))
        raise Exception(msg)

    validatorUtility.diff_key_extractor(ruleEngine.ruleEngine, parent_func_name, stencil_args)

    for parameter, value in stencil_args.items():
        if validatorUtility.validate_value(ruleEngine.ruleEngine, parent_func_name, parameter, value) is False:
            return False
        else:
            continue
    df = eval("businessLogic_{0}.business_logic(spark, **stencil_args)".format(parent_func_name))
    return df
