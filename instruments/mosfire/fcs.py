import inspect
from datetime import datetime, timedelta
from time import sleep

try:
    import ktl
except ModuleNotFoundError as e:
    pass

from .core import *


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def FCS_ok():
    activekw = ktl.cache(keyword='ACTIVE', service='mfcs')
    active = bool(activekw.read())
    if active is not True:
        raise FailedCondition(f'FCS is not active')
    enabledkw = ktl.cache(keyword='ENABLE', service='mfcs')
    enabled = bool(enabledkw.read())
    if enabled is not True:
        raise FailedCondition(f'FCS is not enabled')


##-------------------------------------------------------------------------
## FCS_in_position
##-------------------------------------------------------------------------
def FCS_in_position(PAthreshold=0.5, ELthreshold=0.5,
                   skipprecond=False, skippostcond=False):
    '''Check whether the current FCS position is correcting for the current
    rotator angle and telescope elevation values from dcs.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    FCPA_ELkw = ktl.cache(keyword='PA_EL', service='mfcs')
    FCPA_EL = FCPA_ELkw.read()
    FCSPA = float(FCPA_EL.split()[0])
    FCSEL = float(FCPA_EL.split()[1])
    
    ROTPPOSNkw = ktl.cache(keyword='ROTPPOSN', service='dcs')
    ROTPPOSN = float(ROTPPOSNkw.read())
    ELkw = ktl.cache(keyword='EL', service='dcs')
    EL = float(ELkw.read())
    done = np.isclose(FCSPA, ROTPPOSN, atol=PAthreshold)\
           and np.isclose(FCSEL, EL, atol=ELthreshold)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        FCS_ok()

    return done


##-------------------------------------------------------------------------
## Wait For FCS
##-------------------------------------------------------------------------
def waitfor_FCS(timeout=60, PAthreshold=0.5, ELthreshold=0.5, noshim=False,
                skipprecond=False, skippostcond=False):
    '''Wait for FCS to get close to actual PA and EL.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    log.info('Waiting for FCS to reach destination')
    if noshim is False:
        sleep(0.5)
    done = FCS_in_position(PAthreshold=PAthreshold, ELthreshold=ELthreshold)
    endat = datetime.utcnow() + timedelta(seconds=timeout)
    while done is False and datetime.utcnow() < endat:
        sleep(0.5)
        done = check_FCS(PAthreshold=PAthreshold, ELthreshold=ELthreshold)
    if done is False:
        log.warning(f'Timeout exceeded on waitfor_FCS to finish')
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        FCS_ok()

    return done


##-------------------------------------------------------------------------
## Update FCS
##-------------------------------------------------------------------------
def update_FCS(skipprecond=False, skippostcond=False):
    '''Check whether the current FCS position is correcting for the current
    rotator angle and telescope elevation values from dcs.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    ROTPPOSNkw = ktl.cache(keyword='ROTPPOSN', service='dcs')
    ROTPPOSN = float(ROTPPOSNkw.read())
    ELkw = ktl.cache(keyword='EL', service='dcs')
    EL = float(ELkw.read())

    FCPA_ELkw = ktl.cache(keyword='PA_EL', service='mfcs')
    FCPA_ELkw.write(f"{ROTPPOSN:.2f} {EL:.2f}")

    done = FCS_in_position()

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        FCS_ok()
    
    return done


##-------------------------------------------------------------------------
## Park FCS
##-------------------------------------------------------------------------
def park_FCS(skipprecond=False, skippostcond=False):
    '''Park the FCS in a "nice location" at roughly 4 % range.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    pa_el = ktl.cache(service='mfcs', keyword='pa_el')
    pa_el.write("0.0 43.0")
    sleep(1)
    
    log.info('Disable FCS and pupil rotation')
    fcs_enable = ktl.cache(service='mfcs', keyword='enable')
    fcs_enable.write(0)


    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        FCS_ok()
    
    return done

