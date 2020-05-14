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
#     lockedkw = bool(ktl.cache(service='mmdcs', keyword='LOCKALL'))
#     locked = int(lockedkw.read())
#     if locked == 1:
#         raise FailedCondition(f'Trap door keywords are locked (LOCKALL=1)')
    output = subprocess.run(['show', '-terse', '-s', 'mmdcs', 'lockall'], check=True,
                            stdout=subprocess.PIPE)
    if (output.stdout.decode().strip() == '0') is False:
        raise FailedCondition('Hatch is locked')


##-----------------------------------------------------------------------------
## Lock/Unlock Hatch
##-----------------------------------------------------------------------------
def lock_hatch(skipprecond=False, skippostcond=False):
    '''Lock hatch.
    
    Note: Currently uses subprocess to call to command line show/modify as the
    lockall keyword is not KTL compatible.  -JW (2020-05-11)
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    log.info('Locking hatch')
    log.warning('Using subprocess to call to command line show/modify as the '
                'lockall keyword is not KTL compatible.')
    output = subprocess.run(['modify', '-s', 'mmdcs', 'lockall=1'], check=True,
                            stdout=subprocess.PIPE)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        output = subprocess.run(['show', '-terse', '-s', 'mmdcs', 'lockall'], check=True,
                                stdout=subprocess.PIPE)
        if (output.returncode == 0) is False:
            raise FailedCondition('Hatch is not locked')

    return None


def unlock_hatch(skipprecond=False, skippostcond=False):
    '''Unlock hatch

    Note: Currently uses subprocess to call to command line show/modify as the
    lockall keyword is not KTL compatible.  -JW (2020-05-11)
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    log.info('Unlocking hatch')
    log.warning('Using subprocess to call to command line show/modify as the '
                'lockall keyword is not KTL compatible.')
    output = subprocess.run(['modify', '-s', 'mmdcs', 'lockall=0'], check=True,
                            stdout=subprocess.PIPE)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        hatch_unlocked()

    return None


##-----------------------------------------------------------------------------
## Control Hatch
##-----------------------------------------------------------------------------
def set_hatch(destination, wait=True, timeout=90,
              skipprecond=False, skippostcond=False):
    '''Script to open or close hatch
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
        # Normalize destination
        if destination.lower() in ['open']:
            destination = 'Open'
        elif destination.lower() in ['close', 'closed']:
            destination = 'Closed'

    ##-------------------------------------------------------------------------
    ## Script Contents

    endat = datetime.utcnow() + timedelta(seconds=timeout)
    targname = ktl.cache(service='mmdcs', keyword='TARGNAME')
    posname = ktl.cache(service='mmdcs', keyword='POSNAME')
    posname.monitor()
    if posname == destination:
        log.info(f'Hatich is {posname}')
    else:
        log.info(f"Setting hatch to {destination}")
        targname.write(destination)
        if wait is True:
            sleep(10)
            while posname != destination and datetime.utcnow() < endat:
                sleep(1)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        hatch_ok()
        if posname != destination:
            raise FailedCondition(f"Hatch failed to reach destination")

    return None


##-----------------------------------------------------------------------------
## Open Hatch
##-----------------------------------------------------------------------------
def open_hatch(skipprecond=False, skippostcond=False, wait=True, timeout=60):
    '''Alias for `set_hatch('Open')`
    '''
    set_hatch('Open', wait=wait, timeout=timeout,
              skipprecond=skipprecond, skippostcond=skippostcond)


##-----------------------------------------------------------------------------
## Close Hatch
##-----------------------------------------------------------------------------
def close_hatch(skipprecond=False, skippostcond=False, wait=True, timeout=60):
    '''Alias for `set_hatch('Closed')`
    '''
    set_hatch('Closed', wait=wait, timeout=timeout,
              skipprecond=skipprecond, skippostcond=skippostcond)



##-----------------------------------------------------------------------------
## Aliases
##-----------------------------------------------------------------------------
dustcover_ok = hatch_ok
dustcover_unlocked = hatch_unlocked
trapdoor_ok = hatch_ok
trapdoor_unlocked = hatch_unlocked
