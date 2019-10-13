from .core import *
from .mechs import *
from .detector import *
from time import sleep


def measure_FCS_flexure(rotpposn):
    set_rotpposn(rotpposn)
    set_obsmode('H-spectroscopy')
    waitfor_FCS()
    take_exposure(wait=True)
    go_dark(wait=False)


def measure_FCS_flexure_set(reverse=False):
    rotpposns = [-360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
    if reverse is True:
        rotpposns.reverse()
    for rotpposn in rotpposns:
        measure_FCS_flexure(rotpposn)
        sleep(1)
