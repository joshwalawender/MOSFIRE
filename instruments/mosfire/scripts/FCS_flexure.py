from time import sleep

from ..rotator import *
from ..obsmode import *
from ..fcs import *
from ..detector import *

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
    default="H-spectroscopy",
    help="The obsmode to use (default: H-spectroscopy).")
## add arguments
p.add_argument('argument', type=int,
               help="A single argument")
p.add_argument('allothers', nargs='*',
               help="All other arguments")
args = p.parse_args()


##-------------------------------------------------------------------------
## measure_FCS_flexure
##-------------------------------------------------------------------------
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


##-------------------------------------------------------------------------
## measure_FCS_flexure_set
##-------------------------------------------------------------------------
def measure_FCS_flexure_set(reverse=False, skip=0, obsmode='H-spectroscopy'):
    '''Wraps `measure_FCS_flexure` to take measurements over a range of rotator
    angles.
    '''
    rotpposns = [-360, -315, -270, -225, -180, -135, -90, -45, 0, 45]
    if reverse is True:
        rotpposns.reverse()
    for i in range(skip):
        skipped = rotpposns.pop(0)
        log.info(f'Skipping ROTPPOSN = {skipped}')
    for rotpposn in rotpposns:
        measure_FCS_flexure(rotpposn, obsmode=obsmode)
        sleep(1)


if __name__ == '__main__':
    measure_FCS_flexure_set(reverse=args.reverse, skip=args.skip,
                            obsmode=args.obsmode)
