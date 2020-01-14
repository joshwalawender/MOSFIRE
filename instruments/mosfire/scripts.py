from .core import *
from .mechs import *
from .detector import *
from time import sleep


def measure_FCS_flexure(rotpposn, obsmode='H-spectroscopy', waitforfcs=True):
    '''A simple script used during the FCS flexure measurements.
    
    This script sets a rotator position, an obsmode, then takes an exposure,
    then goes dark.  This would typically be used in a set of measurements
    (taken for example by `measure_FCS_flexure_set`) to get a series of images
    at different rotator angles.
    
    This script would typically be used to take arc lamp spectra of a mask to
    determine flexure by comparing the positions of arc lines in images taken
    over a variety of rotator angles and elevation values.
    
    Under typical use, one would need to turn on the arc lamp manually before
    running this script.
    
    The data taking method used (in Sept & Oct 2019) was:
    * acquire arc lamp spectra at set of rotator angles (using
      `measure_FCS_flexure_set`)
    * do the above at a set of elevation values (e.g. 15, 25, 35, 45, 55, 65,
      75, 85).
    * do the above with the FCS either on or off depending on what is being
      measured.
    * cross correlate the arc lamp spectra to determine how much image motion
      there is due to instrument flexure.
    '''
    set_rotpposn(rotpposn)
    set_obsmode(obsmode)
    if waitforfcs is True:
        waitfor_FCS()
    take_exposure(wait=True)
    go_dark(wait=False)


def measure_FCS_flexure_set(reverse=False, skip=None, obsmode='H-spectroscopy'):
    '''Wraps `measure_FCS_flexure` to take measurements over a range of rotator
    angles.
    '''
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


def measure_single_guider_flexure(obsmode='Y-imaging'):
    update_FCS()
    sleep(2)
    waitfor_FCS()
    take_exposure(wait=True)


def measure_guider_flexure(obsmode='Y-imaging', reverse=False, skip=None):
    '''
    1. OA: Pick a pointing star near desired EL.
    2. OA: Choose rotator position angle (PA) near rotator drive angle -360.
    3. OA: Slew to star using PO REF (rotator mode should be PositionAngle).
    4. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.
    5. SA: Image field in Y-band (to minimize DAR).
    6. OA: Rotate 45 degrees (rotator mode should be PositionAngle).
    7. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.
    8. SA: Image field in Y-band.
    9. Keep repeating steps 7-10 until you have rotated 360 degrees.
    10. Then repeat for a new EL.
    '''
    rotpposns = [-405, -360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
    if reverse is True:
        rotpposns.reverse()
    if skip is not None:
        for i in range(skip):
            skipped = rotpposns.pop(0)
            log.info(f'Skipping ROTPPOSN = {skipped}')

    rotpposn = rotpposns.pop(0)
    print(f'1. OA: Pick a pointing star near desired EL.')
    print(f'2. OA: Slew to star using PO REF (drive angle = {rotpposn}).')
    print(f'3. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.')
    proceed = input('Take image? [y]')
    while proceed.lower() not in ['y', 'yes', 'ok', '']:
        proceed = input('Take image? [y]')
    set_obsmode(obsmode)
    measure_single_guider_flexure(obsmode=obsmode)

    for rotpposn in rotpposns:
        print(f'4. OA: Choose rotator position angle (PA) near rotator drive angle {rotpposn}.')
        print(f'5. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.')
        proceed = input('Take image? [y]')
        while proceed.lower() not in ['y', 'yes', 'ok', '']:
            proceed = input('Take image? [y]')
        measure_single_guider_flexure(obsmode=obsmode)
    go_dark(wait=False)

