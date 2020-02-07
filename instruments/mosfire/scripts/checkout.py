from .core import *
from .mask import *
from .mechs import *
from .detector import *
from .csu import *
from .analysis import *

##-------------------------------------------------------------------------
## MOSFIRE Checkout
##-------------------------------------------------------------------------
def checkout(quick=False):
    '''
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
                'have started the MOSFIRE software AND that the instrument '
                'rotator is not within 10 degrees of a multiple of 180.')
    log.info(intromsg)
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.info('Exiting script.')
        return False
    log.info(f'Executing checkout script.')
    
    log.info('Checking that instrument is dark')
    if not is_dark():
        go_dark()
        waitfor_dark()
    if not is_dark():
        log.error('Could not make instrument dark')
        return False
    log.info('Instrument is dark')

    log.info('Checking mechanisms')
    if check_mechanisms() is True:
        log.info('  Mechanisms ok')
    else:
        log.error('  Mechanism check failed')
        return False

    log.info('Taking dark image')
    set_exptime(2)
    set_coadds(1)
    set_sampmode('CDS')
    sleep(5)
    take_exposure()
    waitfor_exposure()

    log.info(f'Please verify that {lastfile()} looks normal for a dark image')
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.critical('Exiting script.')
        return False

    # Quick checkout
    if quick is True:
        log.info('Setup 2.7x46 long slit mask')
        setup_mask(Mask('2.7x46'))
        waitfor_CSU()
        log.info('Execute mask')
        execute_mask()
        waitfor_CSU()
        set_obsmode('K-imaging', wait=True)
        take_exposure()
        waitfor_exposure()
        wideSlitFile = lastfile()
        go_dark()

        log.info('Setup 0.7x46 long slit mask')
        setup_mask(Mask('0.7x46'))
        waitfor_CSU()
        log.info('Execute mask')
        execute_mask()
        waitfor_CSU()
        set_obsmode('K-imaging', wait=True)
        take_exposure()
        waitfor_exposure()
        wideSlitFile = lastfile()
        go_dark()


    # Normal (long) checkout
    if quick is False:
        log.info('Setup OPEN mask')
        setup_mask(Mask('OPEN'))
        waitfor_CSU()
        execute_mask()
        waitfor_CSU()

