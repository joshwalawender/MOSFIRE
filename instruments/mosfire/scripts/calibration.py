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
## Sub-function: Take Arcs
##-------------------------------------------------------------------------
def take_arcs(filt, cfg):
    # Close hatch
    go_dark()
    close_hatch()
    # Take Ne arcs
    if int(cfg.get(filt, "ne_arc_count", fallback=0)) > 0:
        set_obsmode(f"{filt}-spectroscopy")
        exptime = float(cfg.get(filt, "ne_arc_exptime", fallback=1))
        Ne_lamp('on')
        for i in range(int(cfg.get(filt, "ne_arc_count", fallback=0))):
            take_exposure(exptime=exptime,
                          coadds=int(cfg.get(filt, "ne_arc_coadds", fallback=1)),
                          sampmode=cfg.get(filt, "ne_arc_sampmode", fallback='CDS'),
                          wait=True)
        Ne_lamp('off')
    # Take Ar arcs
    if int(cfg.get(filt, "ar_arc_count", fallback=0)) > 0:
        set_obsmode(f"{filt}-spectroscopy")
        exptime = float(cfg.get(filt, "ar_arc_exptime", fallback=1))
        Ar_lamp('on')
        for i in range(int(cfg.get(filt, "ar_arc_count", fallback=0))):
            take_exposure(exptime=exptime,
                          coadds=int(cfg.get(filt, "ar_arc_coadds", fallback=1)),
                          sampmode=cfg.get(filt, "ar_arc_sampmode", fallback='CDS'),
                          wait=True)
        Ar_lamp('off')
    # Go Dark
    go_dark()


##-------------------------------------------------------------------------
## Sub-function: Take Flats
##-------------------------------------------------------------------------
def take_flats(filt, cfg):
    # Open Hatch
    open_hatch()
    # Turn on dome flat lamps
    dome_flat_lamps(filt)
    # Set mode
    set_obsmode(f"{filt}-spectroscopy")
    # Take flats
    exptime = float(cfg.get(filt, "flat_exptime", fallback=10))
    for i in range(int(cfg.get(filt, "flat_count", fallback=9))):
        take_exposure(exptime=exptime,
                      coadds=int(cfg.get(filt, "flat_coadds", fallback=1)),
                      sampmode=cfg.get(filt, "flat_sampmode", fallback='CDS'),
                      wait=True)
    # Turn off dome flat lamps
    if int(cfg.get(filt, "flatoff_count", fallback=0)) > 0:
        dome_flat_lamps('off')
    # Take lamp off flats
    for i in range(int(cfg.get(filt, "flatoff_count", fallback=0))):
        take_exposure(exptime=exptime,
                      coadds=int(cfg.get(filt, "flat_coadds", fallback=1)),
                      sampmode=cfg.get(filt, "flat_sampmode", fallback='CDS'),
                      wait=True)
    go_dark()


##-------------------------------------------------------------------------
## Take Calibrations for a Single Mask for a List of Bands
##-------------------------------------------------------------------------
def take_mask_calibrations(mask, filters, skipprecond=False, skippostcond=True):
    this_script_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_script_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    cfg_file = Path(args.config).expanduser()
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        mechanisms_ok()
        # Configuration file exists
        if cfg_file.exists() is not True:
            raise FailedCondition(f'Could not find configuration file: {args.config}')
        # Mask input is a mask object
        if not isinstance(mask, Mask):
            mask = Mask(mask)
        # Input filters is list
        if type(filters) is str:
            filters = [filters]

    ##-------------------------------------------------------------------------
    ## Script Contents

    # Read calibration configuration file
    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)

    # Go Dark
    go_dark()
    # Configure CSU
    setup_mask(mask)
    waitfordark()
    execute_mask()
    waitfor_CSU()

    for filt in filters:
        hatch_posname = ktl.cache(service='mmdcs', keyword='POSNAME')
        hatch_posname.monitor()
        if hatch_posname == 'Closed':
            # Start with Arcs
            take_arcs(filt, cfg)
            take_flats(filt, cfg)
        elif hatch_posname == 'Open':
            # Start with Flats
            take_flats(filt, cfg)
            take_arcs(filt, cfg)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        mechanisms_ok()

    return None


##-------------------------------------------------------------------------
## Take Calibrations for All Masks
##-------------------------------------------------------------------------
def take_all_calibrations(masks, config='default_calibrations.cfg',
                          skipprecond=False, skippostcond=True):
    '''Loops over masks and takes calibrations for each.
    
    All masks must have the same calibration configuration file.
    
    Takes an input dictionary containing keys which are Mask objects (or
    resolve to mask objects), and values which are a list of filters.
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

    for entry in masks:
        mask, filters = mask
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None
