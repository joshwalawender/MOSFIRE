from .core import *
from .mechs import *
from .detector import *
from time import sleep

from ktl import Exceptions as ktlExceptions


def set_rotpposn_no_retry(rotpposn):
    log.info(f'Setting ROTPPOSN to {rotpposn:.1f}')
    set('rotdest', rotpposn, service='dcs')
    sleep(1)
    set('rotmode', 'stationary', service='dcs')
    sleep(1)
    done = get('rotstat', service='dcs') == 'in position'
    while done is False:
        sleep(1)
        done = get('rotstat', service='dcs') == 'in position'


def set_rotpposn(rotpposn):
    try:
        set_rotpposn_no_retry(rotpposn)
    except ktlExceptions.ktlError as e:
        log.warning(f"Failed to set rotator")
        log.warning(e)
        sleep(2)
        log.info('Trying again ...')
        set_rotpposn(rotpposn)


def measure_FCS_flexure(rotpposn):
    set_rotpposn(rotpposn)
    set_obsmode('H-spectroscopy')
    take_exposure(wait=True)
    go_dark(wait=False)


def measure_FCS_flexure_set(reverse=False):
    rotpposns = [-360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
    if reverse is True:
        rotpposns.reverse()
    for rotpposn in rotpposns:
        measure_FCS_flexure(rotpposn)
        sleep(1)
