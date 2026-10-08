
# ############################################## Module Information ####################################################
# Module              : dataChecks
# Classes             : N.A.
# Purpose             : Checks for data type
# Consuming module    : stencil
# Created on          : 20-12-2018
# Last changed on     : 03-02-2019
# Last changed by     : Kuldeep singh chauhan
# Reason for change   : Integration
# ######################################################################################################################


def nullable(parameter, value, flag):
    if value is 'None' and flag is False:
        msg="Error: The value {parameter} = {value} doesn't satisfy null check".\
            format(parameter=parameter, value=value)
        status = False
        raise Exception(msg)

    else:
        status = True
    return status

##################################################################################################


def string_flag(parameter, value, flag):
    try:
        if flag is True:
            int(value)
            msg="Error: The value {parameter} = {value} doesn't satisfy string only check".\
                format(parameter=parameter,value=value)
            raise Exception(msg)

    except TypeError:
        return True
    except ValueError:
        return True

##################################################################################################


def integer_flag(parameter, value, flag):
    try:
        if flag is True and type(int(value)) != int:
            msg="Error: The value {parameter} = {value} doesn't satisfy integer only check".\
                format(parameter=parameter,value=value)
            status = False
            raise Exception(msg)
        else:
            status = True
        return status
    except TypeError:
        msg="Error: The value {parameter} = {value} doesn't satisfy integer only check".\
            format(parameter=parameter,value=value)
        raise Exception(msg)
        #return False

    except ValueError:
        msg="Error: The value {parameter} = {value} doesn't satisfy integer only check".\
            format(parameter=parameter, value=value)
        raise Exception(msg)
        #return False

##################################################################################################


def specific_value(parameter, value, listOfValues=[]):
    if value.lower() in listOfValues:
        return True
    else:
        msg = "Error: The value {parameter} = {value} doesn't lie in set {listOfValues} check".\
             format(parameter=parameter,value=value, listOfValues=str(listOfValues))
        #return False
        raise Exception(msg)

##################################################################################################


def range_flag(parameter, value, listOfValues=[]):
    try:
        if int(value) >= listOfValues[0] and int(value) <= listOfValues[1]:
            return True
        else:
            msg = "Error: The value {parameter} = {value} doesn't lie between expected range of {listOfValues}".\
                format(parameter=parameter, value=value, listOfValues=listOfValues)
            #return False
            raise Exception(msg)
    except ValueError:
           msg = "Error: The value {parameter} = {value} doesn't satisfy integer only check".\
                format(parameter=parameter, value=value)
           raise Exception(msg)
    except TypeError:
            msg = "Error: The value {parameter} = {value} doesn't satisfy integer only check".\
               format(parameter=parameter, value=value)
            raise Exception(msg)

##################################################################################################


def list_empty_flag(parameter, value, flag) :
    if flag is True:
        if not value:
            msg="Error: The value {parameter} = {value} is empty".\
                format(parameter=parameter, value=value)
            #return False
            raise Exception(msg)
        else:
            return True

##################################################################################################