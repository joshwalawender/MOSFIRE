from .core import *
from .mechs import *
from .detector import *
from time import sleep


def measure_FCS_flexure(rotpposn, obsmode='H-spectroscopy', waitforfcs=True):
    set_rotpposn(rotpposn)
    set_obsmode(obsmode)
    if waitforfcs is True:
        waitfor_FCS()
    take_exposure(wait=True)
    go_dark(wait=False)


def measure_FCS_flexure_set(reverse=False, skip=None, obsmode='H-spectroscopy'):
    rotpposns = [-360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
    if reverse is True:
        rotpposns.reverse()
    if skip is not None:
        for i in range(skip):
            skipped = rotpposns.pop(0)
            log.info(f'Skipping ROTPPOSN = {skipped}')
    for rotpposn in rotpposns:
        measure_FCS_flexure(rotpposn, obsmode=obsmode)
        sleep(1)
