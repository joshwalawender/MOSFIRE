## Import General Tools
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
def hatch_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the trap door (aka dust cover) status.
    '''
    mmdcs_statuskw = ktl.cache(keyword='STATUS', service='mmdcs')
    hatch_status = mmdcs_statuskw.read()
    if hatch_status != 'OK':
        raise FailedCondition(f'Trap door status is {hatch_status}')


def hatch_unlocked():
    '''Commonly used pre- and post- condition to check whether the mmdcs 
    keywords are locked.
    '''
# NOTE --> This is commented out until we fix the keyword config files to reveal the LOCKALL keyword
    pass
#     lockedkw = bool(ktl.cache(service='mmdcs', keyword='LOCKALL'))
#     locked = int(lockedkw.read())
#     if locked == 1:
#         raise FailedCondition(f'Trap door keywords are locked (LOCKALL=1)')


def dustcover_ok():
    '''Alias for hatch_ok
    '''
    return hatch_ok()


def dustcover_unlocked():
    '''Alias for hatch_unlocked
    '''
    return hatch_unlocked()


def trapdoor_ok():
    '''Alias for hatch_ok
    '''
    return hatch_ok()


def trapdoor_unlocked():
    '''Alias for hatch_unlocked
    '''
    return hatch_unlocked()



##-----------------------------------------------------------------------------
## Instrument Function
##-----------------------------------------------------------------------------
def open_hatch(skipprecond=False, skippostcond=False, wait=True, timeout=60):
    '''docstring
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        hatch_ok()
        hatch_unlocked()
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    endat = datetime.utcnow() + timedelta(seconds=timeout)
    targname = ktl.cache(service='mmdcs', keyword='TARGNAME')
    posname = ktl.cache(service='mmdcs', keyword='POSNAME')
    posname.monitor()

    if posname == 'Open':
        log.info('Hatich is open')
    else:
        log.info(f"Setting hatch to Open")
        targname.write("Open", wait=wait)
        sleep(3)
        while posname != "Open" and datetime.utcnow() < endat:
            sleep(1)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        hatch_ok()

    return None


def close_hatch(skipprecond=False, skippostcond=False, wait=True, timeout=60):
    '''docstring
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        hatch_ok()
        hatch_unlocked()
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    endat = datetime.utcnow() + timedelta(seconds=timeout)
    targname = ktl.cache(service='mmdcs', keyword='TARGNAME')
    posname = ktl.cache(service='mmdcs', keyword='POSNAME')
    posname.monitor()

    if posname == 'Closed':
        log.info('Hatch is closed')
    else:
        log.info(f"Setting hatch to Closed")
        targname.write("Closed", wait=wait)
        sleep(3)
        while posname != "Closed" and datetime.utcnow() < endat:
            sleep(1)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        hatch_ok()

    return None
