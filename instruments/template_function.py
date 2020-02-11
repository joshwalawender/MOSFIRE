import inspect
from datetime import datetime as dt
from datetime import timedelta as tdelta
from time import sleep

import ktl


##-----------------------------------------------------------------------------
## Instrument Function
##-----------------------------------------------------------------------------
def function(arguments, skipprecond=False, skippostcond=False):
    '''docstring
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        if condition1 is not True:
            raise FailedCondition('description of failure')
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    # ----> insert instrument script here <----
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if condition2 is not True:
            raise FailedCondition('description of failure')

    return None
