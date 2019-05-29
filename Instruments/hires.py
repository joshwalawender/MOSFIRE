#!/usr/env/python

## Import General Tools
import argparse
import logging
import re
from datetime import datetime as dt
from time import sleep
import numpy as np
import subprocess


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description='''
''')
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
p.add_argument("-n", "--noactions", dest="noactions",
    default=False, action="store_true",
    help="Run in test mode with no instrument control.")
args = p.parse_args()


##-------------------------------------------------------------------------
## Import KTL python
##-------------------------------------------------------------------------
# Wrap ktl import in try/except so that we can maintain test case or
# simulator version of functions on machines without KTL installed.
if args.noactions is True:
    ktl = None
else:
    try:
        import ktl
    except ModuleNotFoundError:
        ktl = None


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('HIRES')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.DEBUG)
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
## HIRES Properties
##-------------------------------------------------------------------------
name = 'HIRES'
scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
binnings = ["1x1", "1x2", "2x1", "2x2", "3x1"]
serviceNames = ["hires", "hiccd", "expo"]
obstypes = ['Object', 'Dark', 'Line', 'Bias', 'IntFlat', 'DmFlat', 'SkyFlat']
slits = {'B1': (3.5, 0.574),
         'B2': (7.0, 0.574),
         'B3': (14.0, 0.574),
         'B4': (28.0, 0.574),
         'B5': (3.5, 0.861),
         'C1': (7.0, 0.861),
         'C2': (14.0, 0.861),
         'C3': (28.0, 0.861),
         'C4': (3.5, 1.148),
         'C5': (7.0, 1.148),
         'D1': (14.0, 1.148),
         'D2': (28.0, 1.148),
         'D3': (7.0, 1.722),
         'D4': (14.0, 1.722),
         'D5': (0.119, 0.179),
         'E1': (1.0, 0.4),
         'E2': (3.0, 0.4),
         'E3': (5.0, 0.4),
         'E4': (7.0, 0.4),
         'E5': (1.0, 0.8),
         }

# Connect to KTL Services
services = {}
if ktl is not None:
    for service in serviceNames:
        try:
            services[service] = ktl.Service(service)
        except ktl.Exceptions.ktlError:
            print(f"Failed to connect to service {service}")


def get(service, keyword, mode=str):
    if services == {}:
        return None
    assert mode in [str, float, int]
    log.debug(f'Querying {service} for {keyword}')
    kwresult = services[service][keyword].read()
    log.debug(f'  Got result: "{kwresult}"')
    try:
        result = mode(kwresult)
        return result
    except ValueError:
        log.warning(f'Failed to parse {kwresult} as {mode}, returning string')
        return kwresult


def get_collimator():
    '''Determine which collimator is in the beam.  Returns a string of
    'red' or 'blue' indicating which is in beam.  Returns None if it can
    not interpret the result.
    '''
    log.debug('Getting current collimator ...')
    if services == {}:
        return None
    collred = get('hires', 'COLLRED')
    collblue = get('hires', 'COLLBLUE')
    if collred == 'red' and collblue == 'not blue':
        collimator = 'red'
    elif collred == 'not red' and collblue == 'blue':
        collimator = 'blue'
    else:
        collimator = None
    log.debug(f'  collimator = {collimator}')
    return collimator


def lights_are_on():
    '''Returns True if lights are on in the enclosure.
    '''
    log.debug('Getting status of enclosure lights ...')
    if services == {}:
        return None
    lights_str = get('hires', 'lights')
    log.debug(f'  lights are {lights_str}')
    lights = (lights_str == 'on')
    return lights


def get_iodine_temps():
    '''Returns the iodine cell temperatures (tempiod1, tempiod2) in units
    of degrees C.
    '''
    log.debug('Getting iodine cell temperatures ...')
    if services == {}:
        return None
    tempiod1 = get('hires', 'tempiod1', mode=float)
    tempiod2 = get('hires', 'tempiod2', mode=float)
    log.debug(f'  tempiod1 = {tempiod1}')
    log.debug(f'  tempiod2 = {tempiod2}')
    return [tempiod1, tempiod2]


def check_iodine_temps(target1=65, target2=50, range=0.1, wait=False):
    '''Checks the iodine cell temperatures agains the given targets and
    range.  Default values are those used by the CPS team.
    '''
    log.debug('Checking whether iodine cell is at operating temp ...')
    if services == {}:
        return None
    tempiod1, tempiod2 = get_iodine_temps()
    tempiod1_diff = tempiod1 - target1
    tempiod2_diff = tempiod2 - target2
    log.debug(f'  tempiod1 is {tempiod1_diff:.1f} off nominal')
    log.debug(f'  tempiod2 is {tempiod2_diff:.1f} off nominal')
    if abs(tempiod1_diff) < range and abs(tempiod2_diff) < range:
        log.debug('  Iodine temperatures in range')
        return True
    else:
        log.debug('  Iodine temperatures NOT in range')
        if wait is True:
            log.info('  Waiting 10 minutes for iodine cell to reach '
                          'temperature')
            done = ktl.waitFor(f'($hires.TEMPIOD1 > {target1-range}) and '\
                               f'($hires.TEMPIOD1 < {target1+range}) and '\
                               f'($hires.TEMPIOD2 > {target2-range}) and '\
                               f'($hires.TEMPIOD2 < {target2+range})',\
                               timeout=600)
            if done is False:
                logger.warning('Iodine cell did not reach temperature'
                                    'within 10 minutes')
            return done
        else:
            return False


def get_binning():
    '''Return the binning value, a tuple of (binX, binY).
    '''
    log.debug('Getting binning status ...')
    if services == {}:
        return None
    keywordresult = get('hiccd', 'BINNING')
    binningmatch = re.match('\\n\\tXbinning (\d)\\n\\tYbinning (\d)',
                            keywordresult)
    if binningmatch is not None:
        binning = (int(binningmatch.group(1)), int(binningmatch.group(2)))
        log.debug(f'  binning = {binning}')
        return binning
    else:
        log.error(f'Could not parse keyword value "{keywordresult}"')
        return None


def get_windowing():
    '''Return the windowing status.
    '''
    log.debug('Getting windowing status ...')
    if services == {}:
        return None
    keywordresult = get('hiccd', 'WINDOW')
    winmatch = re.match('\\n\\tchip number (\d)\\n\\txstart (\d+)\\n\\t'
                        'ystart (\d+)\\n\\txlen (\d+)\\n\\tylen (\d+)',
                            keywordresult)
    if winmatch is not None:
        window = (int(winmatch.group(1)),
                  int(winmatch.group(2)),
                  int(winmatch.group(3)),
                  int(winmatch.group(4)),
                  int(winmatch.group(5)),
                 )
        log.debug(f'  window = {window}')
        return window
    else:
        log.error(f'Could not parse keyword value "{keywordresult}"')
        return None


def get_gain():
    '''Return the gain as a string 'low' or 'high'.
    '''
    self.log.debug('Getting gain ...')
    if services == {}:
        return None
    gain = get('hiccd', 'CCDGAIN')
    return gain


def get_ccdspeed(self):
    '''Return the CCD readout speed as a string.
    '''
    self.log.debug('Getting CCDSPEED ...')
    if services == {}:
        return None
    speed = get('hiccd', 'CCDSPEED')
    return speed


if __name__ == '__main__':
    pass
