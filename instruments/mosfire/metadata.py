import inspect
import ktl
from time import sleep
from pathlib import Path

from .core import *


##-----------------------------------------------------------------------------
## OUTDIR
##-----------------------------------------------------------------------------
def outdir(skipprecond=False, skippostcond=False):
    '''Return outdir as a pathlib.Path object
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
    OUTDIRkw = ktl.cache(service='mds', keyword='OUTDIR')
    OUTDIRp = Path(OUTDIRkw.read())

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return OUTDIRp


##-----------------------------------------------------------------------------
## set OUTDIR
##-----------------------------------------------------------------------------
def set_outdir(input, skipprecond=False, skippostcond=False):
    '''Return outdir as a pathlib.Path object
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        p = Path(input)
        if not p.parent.exists():
            raise FailedCondition(f'Can not find parent directory for {input}')
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    OUTDIRkw = ktl.cache(service='mds', keyword='OUTDIR')
    OUTDIRkw.write(input)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return None









def filename():
    '''Return the current filename value as a `pathlib.Path` object.
    '''
    return Path(get('FILENAME'))


def lastfile():
    '''Return the last filename value as a `pathlib.Path` object.
    
    This also checks that the file exists.  If it does not, it checks a
    similar path with /s prepended.  This handles the vm-mosfire machine case.
    '''
    lastfile_raw = get('LASTFILE')
    try:
        lastfile = Path(lastfile_raw)
    except:
        log.warning(f'Could not parse "{lastfile_raw}" as a Path')
    else:
        if lastfile.exists():
            return lastfile
        else:
            # Check and see if we need a /s prepended on the path for this machine
            trypath = Path('/s')
            for part in lastfile.parts[1:]:
                trypath = trypath.joinpath(part)
            if not trypath.exists():
                log.warning(f'Could not find last file on disk: {lastfile}')
            else:
                return trypath



def object():
    '''Returns the object string.'''
    return get('OBJECT')


def set_object(input):
    '''Set the object string.'''
    return set('OBJECT', input)


def observer():
    '''Returns the object string.'''
    return get('OBSERVER')


def set_observer(input):
    '''Set the object string.'''
    return set('OBSERVER', input)


