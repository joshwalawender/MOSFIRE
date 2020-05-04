#!kpython3

## Import General Tools
import inspect
from datetime import datetime, timedelta
from time import sleep
from pathlib import Path
import configparser

from ..core import *
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
## Sub-function: Take Arcs
##-------------------------------------------------------------------------
def take_arcs(filt, cfg):
    log.info('Taking arcs')
    # Close hatch
    go_dark()
    close_hatch()
    # Take Ne arcs
    if cfg[filt].getint("ne_arc_count", 0) > 0:
        set_obsmode(f"{filt}-spectroscopy")
        exptime = cfg[filt].getfloat("ne_arc_exptime", 1)
        Ne_lamp('on')
        for i in range(cfg[filt].getint("ne_arc_count", 0)):
            take_exposure(exptime=exptime,
                          coadds=cfg[filt].getint("ne_arc_coadds", 1),
                          sampmode=cfg[filt].get("ne_arc_sampmode", 'CDS'),
                          wait=True)
        Ne_lamp('off')
    # Take Ar arcs
    if cfg[filt].getint("ar_arc_count", 0) > 0:
        set_obsmode(f"{filt}-spectroscopy")
        exptime = cfg[filt].getfloat("ar_arc_exptime", 1)
        Ar_lamp('on')
        for i in range(cfg[filt].getint("ar_arc_count", 0)):
            take_exposure(exptime=exptime,
                          coadds=cfg[filt].getint("ar_arc_coadds", 1),
                          sampmode=cfg[filt].get("ar_arc_sampmode", 'CDS'),
                          wait=True)
        Ar_lamp('off')
    # Go Dark
    go_dark()


##-------------------------------------------------------------------------
## Sub-function: Take Flats
##-------------------------------------------------------------------------
def take_flats(filt, cfg):
    log.info('Taking flats')
    # Open Hatch
    open_hatch()
    # Turn on dome flat lamps
    dome_flat_lamps(filt)
    # Set mode
    set_obsmode(f"{filt}-spectroscopy")
    # Take flats
    exptime = cfg[filt].getfloat("flat_exptime", 10)
    for i in range(cfg[filt].getint("flat_count", 9)):
        take_exposure(exptime=exptime,
                      coadds=cfg[filt].getint("flat_coadds", 1),
                      sampmode=cfg[filt].get("flat_sampmode", 'CDS'),
                      wait=True)
    # Turn off dome flat lamps
    if cfg[filt].getint("flatoff_count", 0) > 0:
        dome_flat_lamps('off')
    # Take lamp off flats
    for i in range(cfg[filt].getint("flatoff_count", 0)):
        take_exposure(exptime=exptime,
                      coadds=cfg[filt].getint("flat_coadds", 1),
                      sampmode=cfg[filt].get("flat_sampmode", 'CDS'),
                      wait=True)
    go_dark()


##-------------------------------------------------------------------------
## Take Calibrations for a Single Mask for a List of Bands
##-------------------------------------------------------------------------
def take_mask_calibrations(mask, filters, cfg,
                           skipprecond=False, skippostcond=True):
    '''Takes calibrations for a single mask in a list of filters.
    '''
    this_script_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_script_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        mechanisms_ok()
        # Mask input is a mask object
        if not isinstance(mask, Mask):
            mask = Mask(mask)
        # Input filters is list
        if type(filters) is str:
            filters = [filters]
        # Filters are in congifuration
        for filt in filters:
            if filt not in cfg.keys():
                raise FailedCondition(f'Filter "{filt}" not in configuration')

    ##-------------------------------------------------------------------------
    ## Script Contents
    log.info(f'Taking calibrations for {mask.name} in filters: {filters}')

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
        else:
            raise FailedCondition(f'Hatch in unknown state: "{hatch_posname}"')

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
def take_all_calibrations(filters, config=None,
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
        # Configuration file exists
        if config in [None, '']:
            log.debug('Using default configuration file')
            config = mosfire_data_file_path / 'scripts' / 'default_calibrations.cfg'
        elif type(config) == dict:
            log.debug('Interpreting configuration input as dict')
        elif type(config) in [str, Path]:
            log.debug('Interpreting configuration input as path')
            config = Path(config).expanduser()
            if config.exists() is not True:
                raise FailedCondition(f'Could not find configuration file: {config}')
        else:
            raise FailedCondition(f'Could not interpret configuration: {config}')

    ##-------------------------------------------------------------------------
    ## Script Contents

    # Read calibration configuration file
    cfg = configparser.ConfigParser()
    if type(config) in [str, Path]:
        cfg.read(config)
    elif type(config) == dict:
        cfg.read_dict(config)

    # Iterate over masks and take cals
    for mask in filters.keys():
        take_mask_calibrations(mask, filters[mask], cfg,
                               skipprecond=skipprecond,
                               skippostcond=skippostcond)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None


if __name__ == '__main__':
    import argparse
    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    ## create a parser object for understanding command-line arguments
    p = argparse.ArgumentParser(description=description)
    ## add options
    p.add_argument("-c", "--config", dest="config", type=str,
        default=None,
        help="The configuration file to use.")
    ## add arguments
    # p.add_argument('argument', type=int,
    #                help="A single argument")
    # p.add_argument('allothers', nargs='*',
    #                help="All other arguments")
    args = p.parse_args()
