#!kpython3

## Import General Tools
import inspect
from datetime import datetime, timedelta
from time import sleep
from pathlib import Path
import argparse
import logging
import configparser

from ..mask import *
from ..filter import *
from ..csu import *
from ..hatch import *
from ..detector import *

try:
    import ktl
except ModuleNotFoundError as e:
    pass

description = '''
This script is intended to replace the mosfireTakeMaskCalibrationData.py script.

Script behavior is powered by a configuration file which contains:

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
## add options
p.add_argument("-c", "--config", dest="config", type=str,
    default="default_calibrations.cfg",
    help="The configuration file to use.")
## add arguments
# p.add_argument('argument', type=int,
#                help="A single argument")
# p.add_argument('allothers', nargs='*',
#                help="All other arguments")
args = p.parse_args()


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('mosfireCalibrations')
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
## The Instrument Script
##-------------------------------------------------------------------------
def take_mask_calibrations(mask, filter, skipprecond=False, skippostcond=True):
    this_script_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_script_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    cfg_file = Path(args.config).expanduser()
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        # Configuration file exists
        if cfg_file.exists() is not True:
            raise FailedCondition(f'Could not find configuration file: {args.config}')
        # Mask input is a mask object
        if not isinstance(mask, Mask):
            mask = Mask(mask)
        instrument_is_MOSFIRE()
        mechanisms_ok()

    ##-------------------------------------------------------------------------
    ## Script Contents

    # Read configuration file
    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)

    # Go Dark
    go_dark()
    waitfordark()
    # Configure CSU
    setup_mask(mask)
    execute_mask()
    waitfor_CSU()
    # Set mode
    set_obsmode(f"{filter}-spectroscopy")
    # Open Hatch
    open_hatch()
    # Turn on dome flat lamps
    turn_on_dome_flat_lamps()
    # Take flats
    exptime = float(cfg.get(filter, "flat_exptime", fallback=10))
    for i in range(int(cfg.get(filter, "flat_count", fallback=9))):
        take_exposure(exptime=exptime,
                      coadds=int(cfg.get(filter, "flat_coadds", fallback=1)),
                      sampmode=cfg.get(filter, "flat_sampmode", fallback='CDS'),
                      wait=True)
    # Turn off dome flat lamps
    turn_off_dome_flat_lamps()
    # Take lamp off flats
    for i in range(int(cfg.get(filter, "flatoff_count", fallback=0))):
        take_exposure(exptime=exptime,
                      coadds=int(cfg.get(filter, "flat_coadds", fallback=1)),
                      sampmode=cfg.get(filter, "flat_sampmode", fallback='CDS'),
                      wait=True)
    # Close hatch
    go_dark()
    close_hatch()
    set_obsmode(f"{filter}-spectroscopy")
    # Take Ne arcs
    Ne_lamp('on')
    for i in range(int(cfg.get(filter, "ne_count", fallback=0))):
        take_exposure(exptime=exptime,
                      coadds=int(cfg.get(filter, "ne_coadds", fallback=1)),
                      sampmode=cfg.get(filter, "ne_sampmode", fallback='CDS'),
                      wait=True)
    Ne_lamp('off')
    # Take Ar arcs
    Ar_lamp('on')
    for i in range(int(cfg.get(filter, "ar_count", fallback=0))):
        take_exposure(exptime=exptime,
                      coadds=int(cfg.get(filter, "ar_coadds", fallback=1)),
                      sampmode=cfg.get(filter, "ar_sampmode", fallback='CDS'),
                      wait=True)
    Ar_lamp('off')
    # Go Dark
    go_dark()

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        mechanisms_ok()

