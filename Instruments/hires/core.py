#!/usr/env/python

## Import General Tools
import sys
from pathlib import Path
import logging

from Instruments import connect_to_ktl, create_log

from ktl import Exceptions as ktlExceptions


##-------------------------------------------------------------------------
## HIRES Properties
##-------------------------------------------------------------------------
name = 'HIRES'
# scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
binnings = ["1x1", "1x2", "2x1", "2x2", "3x1"]
lampnames = ['none', 'ThAr1', 'ThAr2', 'quartz1', 'quartz2']
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

log = create_log(name, loglevel='INFO')
services = connect_to_ktl(name, serviceNames)


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
