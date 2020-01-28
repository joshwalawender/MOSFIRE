def function(arguments, skipprecond=False, skippostcond=False):
    '''docstring
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(arguments, skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            # ----> insert checks here <----
            if condition1 is not True:
                raise FailedPreCondition('description of failure')
            if condition2 is not True:
                raise FailedPreCondition('description of failure')
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(arguments, skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            # ----> insert checks here <----
            if condition3 is not True:
                raise FailedPostCondition('description of failure')
            if condition4 is not True:
                raise FailedPostCondition('description of failure')

    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(arguments, skipprecond=skipprecond)

    # ----> insert instrument script here <----

    postcondition(arguments, skippostcond=skippostcond)

