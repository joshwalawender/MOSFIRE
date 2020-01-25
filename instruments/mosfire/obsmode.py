
##-----------------------------------------------------------------------------
## get obsmode
##-----------------------------------------------------------------------------
def obsmode(skipprecond=False, skippostcond=False):
    '''Return the current observing mode.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            pass
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(skipprecond=skipprecond)

    obsmode = ktl.cache(service='mosfire', keyword='OBSMODE')
    return obsmode.read()

    postcondition(skipprecond=skipprecond)


##-----------------------------------------------------------------------------
## set obsmode
##-----------------------------------------------------------------------------
def set_obsmode(destination, wait=True, timeout=60,
                skipprecond=False, skippostcond=False):
    '''Set the observing mode
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    ##-------------------------------------------------------------------------
    def precondition(destination, skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            # ----> insert checks here <----
            filter, mode = destination.split('-')
            if not mode in modes:
                raise FailedPreCondition(f"Mode: {mode} is unknown")
            if not filter in filters:
                raise FailedPreCondition(f"Filter: {filter} is unknown")
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    ##-------------------------------------------------------------------------
    def postcondition(wait, timeout, skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            if wait is True:
                endat = dt.utcnow() + tdelta(seconds=timeout)
                done = (obsmode().lower() == destination.lower())
                obsmodekw = ktl.cache(service='mosfire', keyword='OBSMODE')
                while not done and dt.utcnow() < endat:
                    sleep(1)
                    done = (obsmodekw.read().lower() == destination.lower())
                if not done:
                    raise FailedPostCondition(f'Timeout exceeded on waiting for mode {destination}')
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    ##-------------------------------------------------------------------------
    precondition(destination, skipprecond=skipprecond)
    
    setobsmodekw = ktl.cache(service='mosfire', keyword='SETOBSMODE')
    log.info(f"Setting mode to {destination}")
    setobsmodekw.write(destination, wait=True)

    postcondition(wait, timeout, skipprecond=skipprecond)
