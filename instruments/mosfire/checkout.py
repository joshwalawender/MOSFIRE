#!kpython3

## Import General Tools
from pathlib import Path

from .core import *
from .mask import Mask
from .filter import is_dark, go_dark
from .obsmode import set_obsmode
from .metadata import lastfile
from .detector import take_exposure
from .csu import setup_mask, execute_mask, initialize_bars
from .rotator import safe_angle
from .domelamps import dome_flat_lamps


##-------------------------------------------------------------------------
## MOSFIRE Checkout
##-------------------------------------------------------------------------
def checkout(quick=False):
    '''Perform a basic checkout of the MOSFIRE instrument.  The normal
    execution of this script performs a standard pre-run checkout.  The quick
    version performs a shorter, less complete checkout to be used when there is
    limited time.

    * Confirm the physical drive angle. It should not be within 10 degrees of a
         multiple of 180 degrees
    * Start the observing software as moseng or the account for the night
    * Check that the dark filter is selected. If not select it
    * Check mechanism status: If any of the mechanisms have a big red X on it,
         you will need to home mechanisms. Note, if filter wheel is at the home
         position, Status will be "OK," position will be "HOME", target will be
         "unknown", and there will still be a big red X.
    * Acquire an exposure
    * Inspect the dark image
    * If normal checkout:
        * Open mask
        * Image and confirm
        * Initialize CSU: modify -s mosfire csuinitbar=0
        * Image and confirm
        * Form 0.7x46 long slit
        * Image and confirm
    * If quick checkout
        * Form an 2.7x46 long slit
        * Image and confirm
        * Form an 0.7x46 long slit
        * Image and confirm
    * With the hatch closed change the observing mode to J-imaging, verify
         mechanisms are ok
    * Quick Dark
    * Message user to verify sidecar logging
    '''

    intromsg = ('This script will do a quick checkout of MOSFIRE.  It should '
                'take about ?? minutes to complete.  Please confirm that you '
                'have started the MOSFIRE software.')
    print(intromsg)
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.info('Exiting script.')
        return False

    instrument_is_MOSFIRE()
    safe_angle()
    log.info(f'Executing checkout script.')
    
    log.info('Checking that instrument is dark')
    if not is_dark():
        log.info('Going dark')
        go_dark()

    log.info('Checking mechanisms')
    mechanisms_ok()

    log.info('Taking dark image')
    take_exposure(exptime=2, coadds=1, sampmode='CDS')

    log.info(f'Please verify that {lastfile()} looks normal for a dark image')
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.critical('Exiting script.')
        return False

    # Quick checkout
    if quick is True:
        log.info('Setup 2.7x46 long slit mask')
        setup_mask(Mask('2.7x46'))
        log.info('Execute mask')
        execute_mask()
        log.info('Taking 2.7" wide long slit image')
        dome_flat_lamps(4)
        set_obsmode('K-imaging')
        take_exposure(exptime=6, coadds=1, sampmode='CDS')
        wideSlitFile = lastfile()
        log.info('Going dark')
        go_dark()

        log.info('Setup 0.7x46 long slit mask')
        setup_mask(Mask('0.7x46'))
        log.info('Execute mask')
        execute_mask()
        log.info('Taking long slit image')
        set_obsmode('K-imaging')
        take_exposure(exptime=6, coadds=1, sampmode='CDS')
        narrowSlitFile = lastfile()
        log.info('Going dark')
        go_dark()
        log.info('Turning dome flat lamps off')
        dome_flat_lamps('off')


    # Normal (long) checkout
    if quick is False:
        log.info('Setup OPEN mask')
        setup_mask(Mask('OPEN'))
        execute_mask()
        log.info('Initializing all bars')
        initialize_bars('all')

        log.info('Taking open mask image')
        dome_flat_lamps(4)
        set_obsmode('K-imaging', wait=True)
        take_exposure(exptime=6, coadds=1, sampmode='CDS')
        openMaskFile = lastfile()
        go_dark()
        
        log.info('Setup 0.7x46 long slit mask')
        setup_mask(Mask('0.7x46'))
        log.info('Execute mask')
        execute_mask()
        log.info('Taking long slit image')
        set_obsmode('K-imaging')
        take_exposure(exptime=6, coadds=1, sampmode='CDS')
        narrowSlitFile = lastfile()
        go_dark()
        log.info('Turning dome flat lamps off')
        dome_flat_lamps('off')



if __name__ == '__main__':
    import argparse
    ## Parse Command Line Arguments
    p = argparse.ArgumentParser(description=description)
    p.add_argument("-q", "--quick", dest="quick",
        default=False, action="store_true",
        help="Do a quick checkout instead of a full checkout.")
    args = p.parse_args()

    checkout(quick=args.quick)
