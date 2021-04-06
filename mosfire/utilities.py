import inspect
from pathlib import Path
import requests
import json
from datetime import datetime

from .core import *
from .mask import Mask


##-----------------------------------------------------------------------------
## Check for Instrument Release
##-----------------------------------------------------------------------------
def check_release(skipprecond=False, skippostcond=False):
    '''Check for instrument release on SIAS.  Return True if released.
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

    now = datetime.now()
    url = 'https://www.keck.hawaii.edu/software/db_api/telSchedule.php?'\
          'cmd=getInstrumentReadyState&instr=MOSFIRE'
    r = requests.get(url)
    result = json.loads(r.text)
    log.info(f'MOSFIRE Release Status = {result.get("State")}')
    released = (result.get("State") == 'Ready')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if result.get('Instrument') != 'MOSFIRE':
            raise FailedCondition('Mismatched instruent from SIAS')
        if result.get('Date') not in [now.strftime('%Y-%m-%d'), now.strftime('%Y%m%d')]:
            raise FailedCondition('Mismatched date from SIAS')

    return released


##-----------------------------------------------------------------------------
## Generate Mask Starlist
##-----------------------------------------------------------------------------
def generate_mask_starlist(masks, filename=None, 
                           skipprecond=False, skippostcond=False):
    '''Generate a starlist file from a list of masks
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

    if filename is None:
        filename = Path('~/mask_starlist.txt').expanduser()
    else:
        filename = Path(filename)

    if filename.exists(): filename.unlink()
    with open(filename, 'a') as starlist:
        for mask in masks:
            if not isinstance(mask, Mask):
                mask = Mask(mask)
            equinox = mask.equinox if hasattr(mask, 'equinox') else 2000
            starlist_line = (f'{mask.name:15s}'
                             f'{mask.center.to_string("hmsdms", sep=" ")} '
                             f'{equinox:7.2f} '
                             f'rotdest={mask.PA:.2f} rotmode=PA')
            print(starlist_line)
            starlist.write(f'{starlist_line}\n')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None
