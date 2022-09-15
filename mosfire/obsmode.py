from .core import *
from ktl.Exceptions import ktlError

##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def grating_shim_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the grating shim status.
    '''
    mmgss_statuskw = ktl.cache(service='mmgss', keyword='STATUS')
    shim_status = mmgss_statuskw.read()
    if shim_status not in ['OK', 'Moving']:
        raise FailedCondition(f'Grating shim status is: "{shim_status}"')


def grating_turret_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the grating turret status.
    '''
    mmgts_statuskw = ktl.cache(service='mmgts', keyword='STATUS')
    turret_status = mmgts_statuskw.read()
    if turret_status not in ['OK', 'Moving']:
        raise FailedCondition(f'Grating turret status is: "{turret_status}"')


##-----------------------------------------------------------------------------
## get obsmode
##-----------------------------------------------------------------------------
def obsmode(skipprecond=False, skippostcond=False):
    '''Return the current observing mode.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        grating_shim_ok()
        grating_turret_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    obsmodekw = ktl.cache(service='mosfire', keyword='OBSMODE')
    obsmode_string = obsmodekw.read()

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        grating_shim_ok()
        grating_turret_ok()

    return obsmode_string


##-----------------------------------------------------------------------------
## set obsmode
##-----------------------------------------------------------------------------
def _set_obsmode(destination, wait=True, timeout=60,
                skipprecond=False, skippostcond=False):
    '''Set the observing mode
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter, mode = destination.split('-')
        # Check valid destination
        if not mode in modes:
            raise FailedPreCondition(f"Mode: {mode} is unknown")
        if not filter in filters and filter != 'dark':
            raise FailedCondition(f"Filter: {filter} is unknown")
        grating_shim_ok()
        grating_turret_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    setobsmodekw = ktl.cache(service='mosfire', keyword='SETOBSMODE')
    log.info(f"Setting mode to {destination}")
    try:
        setobsmodekw.write(destination, wait=True)
    except ktlError as err:
        log.warning(f'Got KTL error: {err}')
        log.warning(f'Retrying after short sleep')
        sleep(2)
        setobsmodekw.write(destination, wait=True)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if wait is True:
            endat = datetime.utcnow() + timedelta(seconds=timeout)
            obsmodekw = ktl.cache(service='mosfire', keyword='OBSMODE')
            done = (obsmodekw.read().lower() == destination.lower())
            while not done and datetime.utcnow() < endat:
                sleep(1)
                done = (obsmodekw.read().lower() == destination.lower())
            if not done:
                raise FailedCondition(f'Timeout exceeded on waiting for mode {destination}')
        grating_shim_ok()
        grating_turret_ok()

    return None


def set_obsmode(destination, wait=True, timeout=60,
                skipprecond=False, skippostcond=False):
    '''Set the observing mode with one retry.
    '''
    try:
        _set_obsmode(destination, wait=wait, timeout=timeout,
                     skipprecond=skipprecond, skippostcond=skippostcond)
    except FailedCondition as e:
        log.warning(f'Timed out waiting for set_obsmode to complete.  Retrying.')
        _set_obsmode(destination, wait=wait, timeout=timeout,
                     skipprecond=skipprecond, skippostcond=skippostcond)
