from instruments import mosfire as m
from time import sleep


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
This script takes a set of exposures at different ROTTPOSN values:
[-360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
It presumes you have configured a mask and turned on  the arc lamps, so that
the arc line positions can be measured to examine flexure.
''')
## add flags
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
## add arguments
p.add_argument('argument', type=int,
               help="A single argument")
p.add_argument('allothers', nargs='*',
               help="All other arguments")
args = p.parse_args()


##-------------------------------------------------------------------------
## measure_single_guider_flexure
##-------------------------------------------------------------------------
def measure_single_guider_flexure(obsmode='Y-imaging'):
    m.update_FCS()
    sleep(2)
    m.waitfor_FCS()
    m.take_exposure(wait=True)


##-------------------------------------------------------------------------
## measure_guider_flexure
##-------------------------------------------------------------------------
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
    m.set_obsmode(obsmode)
    measure_single_guider_flexure(obsmode=obsmode)

    for rotpposn in rotpposns:
        print(f'4. OA: Choose rotator position angle (PA) near rotator drive angle {rotpposn}.')
        print(f'5. OA: Center star on REF using Ca, Ce adjustments ("adjust pointing") and begin guiding.')
        proceed = input('Take image? [y]')
        while proceed.lower() not in ['y', 'yes', 'ok', '']:
            proceed = input('Take image? [y]')
        measure_single_guider_flexure(obsmode=obsmode)
    m.go_dark(wait=False)


if __name__ == '__main__':
    measure_guider_flexure(obsmode=args.obsmode, reverse=args.reverse,
                           skip=args.skip)
