#!/usr/env/python

## Import General Tools
from pathlib import Path
import logging

from datetime import datetime as dt
from time import sleep
import numpy as np
import subprocess
import xml.etree.ElementTree as ET

from astropy.io import fits

from Instruments import connect_to_ktl


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('KeckInstrument')
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
## MOSFIRE Properties
##-------------------------------------------------------------------------
name = 'MOSFIRE'
serviceNames = ['mosfire']
modes = ['Dark Imaging', 'Dark Spectroscopy', 'Imaging', 'Spectroscopy']
filters = ['Y', 'J', 'H', 'K', 'J2', 'J3', 'NB']
allowed_sampmodes = [2, 3]

services = connect_to_ktl(serviceNames)


##-------------------------------------------------------------------------
## Define Common Functions
##-------------------------------------------------------------------------
def get(service, keyword, mode=str):
    """Generic function to get a keyword value.  Converts it to the specified
    mode and does some simple parsing of true and false strings.
    """
    log.debug(f'Querying {service} for {keyword}')
    if services == {}:
        return None
    assert mode in [str, float, int, bool]
    kwresult = services[service][keyword].read()
    log.debug(f'  Got result: "{kwresult}"')

    # Handle string versions of true and false
    if mode is bool:
        if kwresult.strip().lower() == 'false':
            result = False
        elif kwresult.strip().lower() == 'true':
            result = True
        log.debug(f'  Parsed to boolean: {result}')
        return result
    # Convert result to requested type
    try:
        result = mode(kwresult)
        log.debug(f'  Parsed to {mode}: {result}')
        return result
    except ValueError:
        log.warning(f'Failed to parse {kwresult} as {mode}, returning string')
        return kwresult


def set(service, keyword, value, wait=True):
    """Generic function to set a keyword value.
    """
    log.debug(f'Setting {service}.{keyword} to "{value}" (wait={wait})')
    if services == {}:
        return None
    services[service][keyword].write(value, wait=wait)
    log.debug(f'  Done.')


##-------------------------------------------------------------------------
## MOSFIRE Functions
##-------------------------------------------------------------------------
def read_maskfile(xml):
    xmlfile = Path(xml)
    if xmlfile.exists()
        tree = ET.parse(xmlfile)
        root = tree.getroot()
    else:
        try:
            root = ET.fromstring(xml)
        except:
            print(f'Could not parse {xml} as file or XML string')
            raise
    mask = {}
    for child in root:
        if child.tag == 'maskDescription':
            mask['maskDescription'] = child.attrib
        elif child.tag == 'mascgenArguments':
            mask['mascgenArguments'] = {}
            for el in child:
                if el.attrib == {}:
                    mask['mascgenArguments'][el.tag] = (el.text).strip()
                else:
                    print(el.tag, el.attrib)
                    mask['mascgenArguments'][el.tag] = el.attrib
        else:
            mask[child.tag] = [el.attrib for el in child.getchildren()]

    return mask


if __name__ == '__main__':
    pass
