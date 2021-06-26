#! @KPYTHON3@

## Import General Tools
from pathlib import Path
import argparse
import logging
from time import sleep

from mosfire.core import *
from mosfire.fcs import *
from mosfire.detector import *
from mosfire.obsmode import *

description = '''
This script takes a set of exposures at different ROTTPOSN values:
[-360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
It presumes you have configured a mask and turned on  the arc lamps, so that
the arc line positions can be measured to examine flexure.
'''


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description=description)
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
p.add_argument("-r", "--reverse", dest="reverse",
    default=False, action="store_true",
    help="Start with high ROTPPOSN values and iterate lower.")
## add options
p.add_argument("--skip", dest="skip", type=int,
    default=0,
    help="The number of rotator positions to skip (default 0).")
p.add_argument("--obsmode", dest="obsmode", type=str,
    default="Y-imaging",
    help="The obsmode to use (default: Y-imaging).")
args = p.parse_args()


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('GuiderFlexure')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
if args.verbose:
    LogConsoleHandler.setLevel(logging.DEBUG)
else:
    LogConsoleHandler.setLevel(logging.INFO)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
# LogFileName = None
# LogFileHandler = logging.FileHandler(LogFileName)
# LogFileHandler.setLevel(logging.DEBUG)
# LogFileHandler.setFormatter(LogFormat)
# log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## measure_single_guider_flexure
##-------------------------------------------------------------------------
# def measure_single_guider_flexure(obsmode='Y-imaging'):
#     update_FCS()
#     sleep(2)
#     waitfor_FCS()
#     take_exposure(wait=True)


##-------------------------------------------------------------------------
## measure_guider_flexure
##-------------------------------------------------------------------------
# def measure_guider_flexure(obsmode='Y-imaging', reverse=False, skip=0):
#     '''
#     1. OA: Pick a pointing star near desired EL.
#     2. OA: Choose rotator position angle (PA) near rotator drive angle -360.
#     3. OA: Slew to star using PO REF (rotator mode should be PositionAngle).
#     4. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.
#     5. SA: Image field in Y-band (to minimize DAR).
#     6. OA: Rotate 45 degrees (rotator mode should be PositionAngle).
#     7. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.
#     8. SA: Image field in Y-band.
#     9. Keep repeating steps 7-10 until you have rotated 360 degrees.
#     10. Then repeat for a new EL.
#     '''
#     rotpposns = [-405, -360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
#     if reverse is True:
#         rotpposns.reverse()
#     for i in range(skip):
#         skipped = rotpposns.pop(0)
#         log.info(f'Skipping ROTPPOSN = {skipped}')
# 
#     rotpposn = rotpposns.pop(0)
#     print(f'1. OA: Pick a pointing star near desired EL.')
#     print(f'2. OA: Slew to star using PO REF (drive angle = {rotpposn}).')
#     print(f'3. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.')
#     proceed = input('Take image? [y]')
#     while proceed.lower() not in ['y', 'yes', 'ok', '']:
#         proceed = input('Take image? [y]')
#     set_obsmode(obsmode)
#     measure_single_guider_flexure(obsmode=obsmode)
# 
#     for rotpposn in rotpposns:
#         print(f'4. OA: Choose rotator position angle (PA) near rotator drive angle {rotpposn}.')
#         print(f'5. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.')
#         proceed = input('Take image? [y]')
#         while proceed.lower() not in ['y', 'yes', 'ok', '']:
#             proceed = input('Take image? [y]')
#         measure_single_guider_flexure(obsmode=obsmode)
#     go_dark(wait=False)


if __name__ == '__main__':
    foo = obsmode()
    print(foo)
#     measure_guider_flexure(obsmode=args.obsmode, reverse=args.reverse,
#                            skip=args.skip)
