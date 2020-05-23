import inspect
from pathlib import Path
import subprocess
import sys


from .core import *
from .fcs import park_FCS
from .hatch import close_hatch, lock_hatch
from .filter import go_dark
from .domelamps import dome_flat_lamps
from .power import Ne_lamp, Ar_lamp


##-----------------------------------------------------------------------------
## Stop MOSFIRE Software
##-----------------------------------------------------------------------------
def stop_mosfire_software(skipprecond=False, skippostcond=False):
    '''Stop MOSFIRE Software.  Calls `mosfireStop` script via subprocess.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    log.info('Calling the mosfireStop command line script')
    output = subprocess.run(['mosfireStop'], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in output.stdout.decode().split('\n'):
        log.debug(f'STDOUT: {line}')
    for line in output.stderr.decode().split('\n'):
        log.debug(f'STDERR: {line}')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None


##-----------------------------------------------------------------------------
## End of Night Shutdown
##-----------------------------------------------------------------------------
def end_of_night_shutdown(skipprecond=False, skippostcond=False):
    '''End of night shutdown
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    log.info('-------------------------------------------------------------')
    log.info("You have started the end-of-night shutdown script.")
    log.info("This script will do the following.")
    log.info(" - close the dust cover and disable motion.")
    log.info(" - configure for dark-spectroscopy")
    log.info(" - disable FCS")
    log.info(" - halt watch processes")
    log.info(" - shutdown all guis")
    log.info('-------------------------------------------------------------')

    # Insert the dark filter
    log.info('Going dark')
    go_dark()
    # Close the dust cover
    log.info('Closing hatch')
    close_hatch()
    # Put FCS in a nice location and disableFCS&pupil rotation
    log.info('Parking FCS')
    park_FCS()
    # Stop the MOSFIRE software
    log.info('Stopping MOSFIRE software')
    stop_mosfire_software()
    # Disable the hatch
    log.info('Locking mechanisms')
    lock_hatch()
    # Ensure the internal MOSFIRE lamps are off
    log.info('Internal lamps (Ne, Ar) off')
    Ne_lamp('off')
    Ar_lamp('off')
    # If MOSFIRE is the current instrument, ensure the dome lamps are off
    INSTRUMEkw = ktl.cache(service='dcs', keyword='INSTRUME')
    if INSTRUMEkw.read() == 'MOSFIRE':
        log.info('Turning off dome lamps')
        dome_flat_lamps('off')

    log.info('-------------------------------------------------------------')
    log.info('     MOSFIRE Instrument End-of-Night shutdown complete')
    log.info('-------------------------------------------------------------')


    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None
