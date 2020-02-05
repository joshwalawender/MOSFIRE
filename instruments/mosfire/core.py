from pathlib import Path
import yaml
from datetime import datetime as dt
from datetime import timedelta as tdelta
from time import sleep
import numpy as np

from instruments import create_log, FailedCondition


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
## pre- and post- conditions
##-----------------------------------------------------------------------------
def filter1_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the filter wheel status.
    '''
    # Check filter wheel 1 status
    mmf1s_status = ktl.cache(service='mmf1s', keyword='STATUS')
    filter1_status = mmf1s_status.read()
    if filter1_status != 'OK':
        raise FailedCondition(f'Filter 1 status is not OK: "{filter1_status}"')


def filter2_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the filter wheel status.
    '''
    # Check filter wheel 2 status
    mmf2s_status = ktl.cache(service='mmf2s', keyword='STATUS')
    filter2_status = mmf2s_status.read()
    if filter2_status != 'OK':
        raise FailedCondition(f'Filter 2 status is not OK: "{filter2_status}"')


def FCS_ok():
    activekw = ktl.cache(keyword='ACTIVE', service='mfcs')
    active = bool(activekw.read())
    if active is not True:
        raise FailedCondition(f'FCS is not active')
    enabledkw = ktl.cache(keyword='ENABLE', service='mfcs')
    enabled = bool(enabledkw.read())
    if enabled is not True:
        raise FailedCondition(f'FCS is not enabled')


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


def check_mechanisms():
    '''Simple loop to check all mechanisms.
    '''
    log.info('Checking mechanisms')
    mechs = ['filter1', 'filter2', 'FCS', 'grating_shim', 'grating_turret',
             'pupil_rotator', 'trapdoor']
    for mech in mechs:
        statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
        statusfn()


def bar_ok(barnum):
    '''Commonly used pre- and post- condition to check whether there are errors
    in the CSU bar status for a specified bar.
    '''
    bstatkw = ktl.cache(keyword=f"B{int(barnum):02d}STAT", service='mcsus')
    bar_status = bstatkw.read()
    if bar_status != 'OK':
        raise FailedCondition(f'Bar {int(barnum):02d} status is {bar_status}')


def CSUbars_ok():
    '''Simple loop to check all bars in the CSU.
    '''
    for barnum in range(1,93,1):
        bar_ok(barnum)


def CSUready():
    '''Commonly used pre- and post- condition to check whether the CSU is ready
    for a move.
    '''
    csureadykw = ktl.cache(keyword='CSUREADY', service='mcsus')
    csuready = int(csureadykw.read())
    translation = {0: 'Unknown',
                   1: 'System Started',
                   2: 'Ready for Move',
                   3: 'Moving',
                   4: 'Configuring',
                   -1: 'Error',
                   -2: 'System Stopped'}[csuready]
    if csuready == -1:
        raise CSUFatalError
    if csuready != 2:
        raise FailedCondition(f'CSU is not ready: {translation}')
