import inspect
import numpy as np

import ktl

from .core import *

##-------------------------------------------------------------------------
## pre- and post- conditions
##-------------------------------------------------------------------------
def FCS_ok():
    activekw = ktl.cache(keyword='ACTIVE', service='mfcs')
    activekw.monitor()
    if bool(activekw) is not True:
        raise FailedPrePostCondition(f'FCS is not active')
    enabledkw = ktl.cache(keyword='ENABLE', service='mfcs')
    enabledkw.monitor()
    if bool(enabledkw) is not True:
        raise FailedPrePostCondition(f'FCS is not enabled')


##-------------------------------------------------------------------------
## FCS_in_position
##-------------------------------------------------------------------------
def FCS_in_position(PAthreshold=0.5, ELthreshold=0.5,
                   skipprecond=False, skippostcond=False):
    '''Check whether the current FCS position is correcting for the current
    rotator angle and telescope elevation values from dcs.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    precondition(skipprecond=skipprecond)

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

    postcondition(skippostcond=skippostcond)

    return done


##-------------------------------------------------------------------------
## FCS_up_to_date
##-------------------------------------------------------------------------
def update_FCS(skipprecond=False, skippostcond=False):
    '''Check whether the current FCS position is correcting for the current
    rotator angle and telescope elevation values from dcs.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(arguments, skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(arguments, skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            FCS_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    precondition(skipprecond=skipprecond)
    
    ROTPPOSNkw = ktl.cache(keyword='ROTPPOSN', service='dcs')
    ROTPPOSN = ROTPPOSNkw.read()
    ELkw = ktl.cache(keyword='EL', service='dcs')
    EL = ELkw.read()

    FCPA_ELkw = ktl.cache(keyword='PA_EL', service='mfcs')
    FCPA_ELkw.write(f"{ROTPPOSN:.2f} {EL:.2f}")

    done = FCS_in_position()

    postcondition(skippostcond=skippostcond)

    return done












# def waitfor_FCS(timeout=60, PAthreshold=0.5, ELthreshold=0.5, noshim=False):
#     '''Wait for FCS to get close to actual PA and EL.
#     '''
#     log.info('Waiting for FCS to reach destination')
#     if noshim is False:
#         sleep(1)
#     done = check_FCS(PAthreshold=PAthreshold, ELthreshold=ELthreshold)
#     endat = dt.utcnow() + tdelta(seconds=timeout)
#     while done is False and dt.utcnow() < endat:
#         sleep(1)
#         done = check_FCS(PAthreshold=PAthreshold, ELthreshold=ELthreshold)
#     if done is False:
#         log.warning(f'Timeout exceeded on waitfor_FCS to finish')
#     return done
