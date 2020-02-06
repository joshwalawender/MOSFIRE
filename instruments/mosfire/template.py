import inspect
import ktl
from time import sleep


##-----------------------------------------------------------------------------
## Instrument Function
##-----------------------------------------------------------------------------
def function(arguments, skipprecond=False, skippostcond=False):
    '''docstring
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            # ----> insert checks here <----
            if condition1 is not True:
                raise FailedCondition('description of failure')
            if condition2 is not True:
                raise FailedCondition('description of failure')
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            # ----> insert checks here <----
            if condition3 is not True:
                raise FailedCondition('description of failure')
            if condition4 is not True:
                raise FailedCondition('description of failure')
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    precondition(skipprecond=skipprecond)

    # ----> insert instrument script here <----

    postcondition(skippostcond=skippostcond)

    return None
