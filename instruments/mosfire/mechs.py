from .core import *

import numpy as np

##-------------------------------------------------------------------------
## MOSFIRE Status Check Functions
##-------------------------------------------------------------------------
def grating_shim_ok():
    return get('MGSSTAT') == 'OK'


def grating_turret_ok():
    return get('MGTSTAT') == 'OK'


def grating_ok():
    return get('GRATSTAT') == 'OK'


def filter1_ok():
    return get('MF1STAT') == 'OK'


def filter2_ok():
    return get('MF2STAT') == 'OK'


def filters_ok():
    return get('FILTSTAT') == 'OK'


def fcs_ok():
    return get('FCSSTAT') == 'OK'


def pupil_rotator_ok():
    return get('MPRSTAT') in ['OK', 'Tracking']


def trapdoor_ok():
    return dustcover_ok()


def dustcover_ok():
    return get('MDCSTAT') == 'OK'


def check_mechanisms():
    log.info('Checking mechanisms')
    mechs = ['filter1', 'filter2', 'fcs', 'grating_shim', 'grating_turret',
             'pupil_rotator', 'trapdoor', 'FCS']
    for mech in mechs:
        statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
        ok = statusfn()
        if ok is False:
            log.error(f'{mech} status is not ok')
            log.error(f'Please address the problem, then re-run the checkout.')
            return False
    return True


