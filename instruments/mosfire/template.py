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
    postcondition(arguments, skipprecond=skipprecond)









##-----------------------------------------------------------------------------
## get
##-----------------------------------------------------------------------------
def get(keyword, service='mosfire', mode=str):
    """Generic function to get a keyword value.  Converts it to the specified
    mode and does some simple parsing of true and false strings.
    """
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    ##-------------------------------------------------------------------------
    def precondition(arguments, skipprecond=False):
        '''Check that the keyword service is available.
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            if service not in services.keys():
                raise FailedPreCondition(f'Not connected to service "{service}"')
            if mode not in [str, float, int, bool]:
                raise FailedPreCondition(f'Mode "mode" not an allowed value')
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    ##-------------------------------------------------------------------------
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
    ##-------------------------------------------------------------------------
    precondition(arguments, skipprecond=skipprecond)

    # ----> insert instrument script here <----    
    log.debug(f'Querying {service} for {keyword}')
    kwresult = services[service][keyword].read()
    log.debug(f'  Got result: "{kwresult}"')
    # Handle string versions of true and false
    if mode is bool:
        if kwresult.strip().lower() == 'false':
            result = False
        elif kwresult.strip().lower() == 'true':
            result = True
        else:
            try:
                result = bool(int(kwresult))
            except:
                result = None
        if result is not None:
            log.debug(f'  Parsed to boolean: {result}')
        else:
            log.error(f'  Failed to parse "{kwresult}"')
        return result
    # Convert result to requested type
    try:
        result = mode(kwresult)
        log.debug(f'  Parsed to {mode}: {result}')
        return result
    except ValueError:
        log.warning(f'Failed to parse {kwresult} as {mode}, returning string')
        return kwresult

    postcondition(arguments, skipprecond=skipprecond)


