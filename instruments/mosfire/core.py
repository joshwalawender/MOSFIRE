from pathlib import Path
import yaml
from datetime import datetime as dt
from datetime import timedelta as tdelta
import numpy as np

from instruments import create_log


class FailedCondition(Exception):
    def __init__(self, message):
        self.message = message
        log.error('Failed pre- or post- condition check')
        log.error(f'  {self.message}')


class CSUFatalError(Exception):
    def __init__(self, *args):
        log.error('The CSU has experienced a Fatal Error')


##-------------------------------------------------------------------------
## MOSFIRE Properties
##-------------------------------------------------------------------------
name = 'MOSFIRE'
serviceNames = ['mosfire', 'mmf1s', 'mmf2s', 'mcsus', 'mfcs', 'mds', 'dcs']
modes = ['dark-imaging', 'dark-spectroscopy', 'imaging', 'spectroscopy']
filters = ['Y', 'J', 'H', 'K', 'J2', 'J3', 'NB']
csu_bar_state_file = Path('/s/sdata1300/logs/server/mcsus/csu_bar_state')

allowed_sampmodes = [2, 3]
sampmode_names = {'CDS': (2, None), 'MCDS': (3, None), 'MCDS16': (3, 16)}

# Load default CSU coordinate transformations
filepath = Path(__file__).parent
with open(filepath.joinpath('MOSFIRE_transforms.txt'), 'r') as FO:
    Aphysical_to_pixel, Apixel_to_physical = yaml.safe_load(FO.read())
Aphysical_to_pixel = np.array(Aphysical_to_pixel)
Apixel_to_physical = np.array(Apixel_to_physical)

log = create_log(name, loglevel='DEBUG')


##-----------------------------------------------------------------------------
## pre- and post- conditions for other mechanisms
##-----------------------------------------------------------------------------
def pupil_rotator_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the pupil rotator status.
    '''
    mmprs_statuskw = ktl.cache(keyword='STATUS', service='mmprs')
    pupil_status = mmprs_statuskw.read()
    if pupil_status != 'OK':
        raise FailedCondition(f'Pupil rotator status is {pupil_status}')


def trapdoor_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the trap door (aka dust cover) status.
    '''
    mmdcs_statuskw = ktl.cache(keyword='STATUS', service='mmdcs')
    trapdoor_status = mmdcs_statuskw.read()
    if trapdoor_status != 'OK':
        raise FailedCondition(f'Trap door status is {trapdoor_status}')


def dustcover_ok():
    '''Alias for trapdoor_ok
    '''
    return trapdoor_ok


# def check_mechanisms():
#     '''Simple loop to check all mechanisms.
#     '''
#     log.info('Checking mechanisms')
#     mechs = ['filter1', 'filter2', 'FCS', 'grating_shim', 'grating_turret',
#              'pupil_rotator', 'trapdoor']
#     for mech in mechs:
#         statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
#         statusfn()



##-----------------------------------------------------------------------------
## Rotator Control
##-----------------------------------------------------------------------------
def _set_rotpposn(rotpposn, skipprecond=False, skippostcond=False):
    '''Set the rotator position in stationary mode.
    
    This only tries to set the position once, use `set_rotpposn` in practice
    as it makes multiple attempts which seems to be more reliable.
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

    log.info(f'Setting ROTPPOSN to {rotpposn:.1f}')
    ROTDESTkw = ktl.cache(service='dcs', keyword='ROTDEST')
    ROTDESTkw.write(float(rotpposn))
    sleep(1)
    ROTMODEkw = ktl.cache(service='dcs', keyword='ROTMODE')
    ROTMODEkw.write('stationary')
    sleep(1)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        log.info(f'Waiting for rotator to be "in position"')
        ROTSTATkw = ktl.cache(service='dcs', keyword='ROTSTAT')
        ROTSTATkw.monitor()
        while str(ROTSTATkw) != 'in position':
            log.debug(f'ROTSTAT = "{ROTSTATkw}"')
            sleep(2)

    return None


def set_rotpposn(rotpposn):
    '''Set the rotator position in stationary mode.  Performs a single retry if
    a ktlError is raised.
    '''
    try:
        _set_rotpposn(rotpposn)
    except ktlExceptions.ktlError as e:
        log.warning(f"Failed to set rotator")
        log.warning(e)
        sleep(2)
        log.info('Trying again ...')
        _set_rotpposn(rotpposn)
