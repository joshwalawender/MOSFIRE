#!kpython3

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
    '''
    instrument_is_MOSFIRE()
    safe_angle()
    log.info(f'Executing checkout script.')

    log.info('Checking that instrument is dark')
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

    # Normal (long) checkout
    if quick is False:
        log.info('Setup OPEN mask')
        setup_mask(Mask('OPEN'))
        execute_mask()
        log.info('Initializing all bars')
        initialize_bars('all')

        log.info('Taking open mask image')
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


if __name__ == '__main__':
    import argparse
    ## Parse Command Line Arguments
    p = argparse.ArgumentParser(description=description)
    p.add_argument("-q", "--quick", dest="quick",
        default=False, action="store_true",
        help="Do a quick checkout instead of a full checkout.")
    args = p.parse_args()

    checkout(quick=args.quick)
