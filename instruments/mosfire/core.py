import inspect
from pathlib import Path
import yaml
import numpy as np
import socket
import subprocess
import sys

try:
    import ktl
except ModuleNotFoundError as e:
    pass

from instruments import create_log


##-------------------------------------------------------------------------
## Define Exceptions
##-------------------------------------------------------------------------
class FailedCondition(Exception):
    def __init__(self, message):
        self.message = message
        log.error('Failed pre- or post- condition check')
        log.error(f'  {self.message}')


class CSUFatalError(Exception):
    def __init__(self, *args):
        log.error('The CSU has experienced a Fatal Error')


##-------------------------------------------------------------------------
## MOSFIRE Properties
##-------------------------------------------------------------------------
name = 'MOSFIRE'
modes = ['dark-imaging', 'dark-spectroscopy', 'imaging', 'spectroscopy']
filters = ['Y', 'J', 'H', 'K', 'J2', 'J3', 'NB']
csu_bar_state_file = Path('/s/sdata1300/logs/server/mcsus/csu_bar_state')

# Load default CSU coordinate transformations
mosfire_data_file_path = Path(__file__).parent
with open(mosfire_data_file_path.joinpath('MOSFIRE_transforms.txt'), 'r') as FO:
    transforms = yaml.safe_load(FO.read())
Aphysical_to_pixel = np.array(transforms['Aphysical_to_pixel'])
Apixel_to_physical = np.array(transforms['Apixel_to_physical'])

log = create_log(name, loglevel='DEBUG')

from .fcs import park_FCS
from .hatch import close_hatch, lock_hatch
from .filter import go_dark
from .domelamps import dome_flat_lamps
from .power import Ne_lamp, Ar_lamp


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def instrument_is_MOSFIRE():
    '''Verifies that MOSFIRE is the currently selected instrument.
    '''
    INSTRUMEkw = ktl.cache(service='dcs', keyword='INSTRUME')
    if INSTRUMEkw.read() != 'MOSFIRE':
        raise FailedCondition('MOSFIRE is not the selected instrument')


def check_connectivity():
    '''Pings the two switches on the instrument to verify network connectivity.
    '''
    host = socket.gethostname()
    addresses = ['192.168.13.11', '192.168.13.12']
    if host == 'mosfireserver':
        raise NotImplementedError
    elif host == 'mosfire':
        for address in addresses:
            log.debug(f"Checking ping to {address}")
            cmd = ['ssh', 'mosfireserver', f"ping {address}"]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = result.stdout.decode().strip('\n')
            stderr = result.stderr.decode().strip('\n')
            log.debug(stdout)
            if stderr != '': log.debug(stderr)
            if bool(result.returncode):
                raise FailedCondition(f"ping {address}: {stdout} {stderr}")


def pupil_rotator_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the pupil rotator status.
    '''
    mmprs_statuskw = ktl.cache(keyword='STATUS', service='mmprs')
    pupil_status = mmprs_statuskw.read()
    if pupil_status not in ['OK', 'TRACKING']:
        raise FailedCondition(f'Pupil rotator status is {pupil_status}')


def mechanisms_ok():
    '''Simple loop to check whether there are errors in the status of all
    mechanisms.
    '''
    log.info('Checking mechanisms')
    mechs = ['filter1', 'filter2', 'FCS', 'grating_shim', 'grating_turret',
             'pupil_rotator', 'hatch']
    for mech in mechs:
        statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
        statusfn()


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
