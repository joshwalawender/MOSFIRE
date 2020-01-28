from datetime import datetime as dt
from datetime import timedelta as tdelta
import ktl

from .core import *


##-----------------------------------------------------------------------------
## get obsmode
##-----------------------------------------------------------------------------
def obsmode(skipprecond=False, skippostcond=False):
    '''Return the current observing mode.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=skipprecond):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            pass
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=skippostcond):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(skipprecond=skipprecond)

    obsmodekw = ktl.cache(service='mosfire', keyword='OBSMODE')
    obsmode_string = obsmodekw.read()

    postcondition(skippostcond=skippostcond)

    return obsmode_string


##-----------------------------------------------------------------------------
## set obsmode
##-----------------------------------------------------------------------------
def set_obsmode(destination, wait=True, timeout=60,
                skipprecond=False, skippostcond=False):
    '''Set the observing mode
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(destination, skipprecond=skipprecond):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            # ----> insert checks here <----
            filter, mode = destination.split('-')
            # Check valid destination
            if not mode in modes:
                raise FailedPreCondition(f"Mode: {mode} is unknown")
            if not filter in filters and filter != 'dark':
                raise FailedPreCondition(f"Filter: {filter} is unknown")
            # Check grating turret status
            mmgts_statuskw = ktl.cache(service='mmgts', keyword='STATUS')
            turret_status = mmgts_statuskw.read()
            if turret_status != 'OK':
                raise FailedPreCondition(f'Grating turret status is not OK: "{turret_status}"')
            # Check grating shim status
            mmgss_statuskw = ktl.cache(service='mmgss', keyword='STATUS')
            shim_status = mmgss_statuskw.read()
            if shim_status != 'OK':
                raise FailedPreCondition(f'Grating shim status is not OK: "{shim_status}"')
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(wait, timeout, skippostcond=skippostcond):
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
                # Check grating turret status
            mmgts_statuskw = ktl.cache(service='mmgts', keyword='STATUS')
            turret_status = mmgts_statuskw.read()
            if turret_status != 'OK':
                raise FailedPostCondition(f'Grating turret status is not OK: "{turret_status}"')
            # Check grating shim status
            mmgss_statuskw = ktl.cache(service='mmgss', keyword='STATUS')
            shim_status = mmgss_statuskw.read()
            if shim_status != 'OK':
                raise FailedPostCondition(f'Grating shim status is not OK: "{shim_status}"')

    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(destination, skipprecond=skipprecond)
    
    setobsmodekw = ktl.cache(service='mosfire', keyword='SETOBSMODE')
    log.info(f"Setting mode to {destination}")
    setobsmodekw.write(destination, wait=True)

    postcondition(wait, timeout, skippostcond=skippostcond)
