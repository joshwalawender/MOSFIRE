import inspect
from pathlib import Path
import logging
import yaml
import numpy as np
import socket
import subprocess
import sys
from datetime import datetime, timedelta
from time import sleep

try:
    import ktl
except:
    print('Failed to import ktl')
    sys.exit(1)


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_log(name='MOSFIRE', loglevel=logging.INFO, logfile=None):
    if type(loglevel) == str:
        loglevel = getattr(logging, loglevel.upper())
    log = logging.getLogger(name)
    if len(log.handlers) == 0:
        log.setLevel(logging.DEBUG)
        ## Set up console output
        LogConsoleHandler = logging.StreamHandler()
        LogConsoleHandler.setLevel(loglevel)
        LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
        LogConsoleHandler.setFormatter(LogFormat)
        log.addHandler(LogConsoleHandler)
        ## Set up file output
        if logfile is not None:
            logfile = Path(logfile).expanduser()
            if logfile.parent.exists() and logfile.parent.is_dir():
                LogFileHandler = logging.FileHandler(logfile)
                LogFileHandler.setLevel(logging.DEBUG)
                LogFileHandler.setFormatter(LogFormat)
                log.addHandler(LogFileHandler)
    return log


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
filters = ['Y', 'J', 'H', 'K', 'Ks', 'J2', 'J3', 'nb1061']
csu_bar_state_file = Path('/s/sdata1300/logs/server/mcsus/csu_bar_state')
mosfire_data_file_path = Path(__file__).parent
# Load default CSU coordinate transformations
with open(mosfire_data_file_path.joinpath('MOSFIRE_transforms.txt'), 'r') as FO:
    transforms = yaml.safe_load(FO.read())

log = create_log(name, loglevel='INFO', logfile='~/mosfire.log')

from .fcs import FCS_ok
from .hatch import hatch_ok
from .filter import filter1_ok, filter2_ok
from .obsmode import grating_shim_ok, grating_turret_ok


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
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
    if pupil_status not in ['OK', 'Tracking']:
        raise FailedCondition(f'Pupil rotator status is {pupil_status}')


def mechanisms_ok():
    '''Simple loop to check whether there are errors in the status of all
    mechanisms.
    '''
    log.debug('Checking mechanisms')
    mechs = ['filter1', 'filter2', 'FCS', 'grating_shim', 'grating_turret',
             'pupil_rotator', 'hatch']
    for mech in mechs:
        statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
        statusfn()


##-----------------------------------------------------------------------------
## scriptrun functions
##-----------------------------------------------------------------------------
def start_scriptrun():
    scriptrun = ktl.cache(keyword='scriptrun', service='mosfire')
    if int(scriptrun.read()) == 1:
        raise FailedCondition('SCRIPTRUN is already set')
    scriptrun.write(1, wait=True)


def stop_scriptrun():
    scriptrun = ktl.cache(keyword='scriptrun', service='mosfire')
    scriptrun.write(0, wait=True)


reset_scriptrun = stop_scriptrun
