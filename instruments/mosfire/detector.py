import inspect
import ktl
from time import sleep
import re

from .core import *
from .metadata import *
from .fcs import *


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def waitfor_exposure(timeout=240, shim=False):
    '''Block and wait for the current exposure to be complete.
    '''
    log.debug('Waiting for exposure to finish')
    endat = dt.utcnow() + tdelta(seconds=timeout)
    if shim is True:
        sleep(1)
    IMAGEDONEkw = ktl.cache(service='mds', keyword='IMAGEDONE')
    IMAGEDONEkw.monitor()
    READYkw = ktl.cache(service='mds', keyword='READY')
    READYkw.monitor()

    done_and_ready = bool(IMAGEDONEkw) and bool(READYkw)
    while dt.utcnow() < endat and not done_and_ready:
        sleep(1)
        done_and_ready = bool(IMAGEDONEkw) and bool(READYkw)
    if not done_and_ready:
        raise FailedCondition('Timeout exceeded on waitfor_exposure to finish')


def wfgo(timeout=240, shim=False):
    '''Alias waitfor_exposure to wfgo
    '''
    waitfor_exposure(timeout=timeout, shim=shim)


##-----------------------------------------------------------------------------
## exptime
##-----------------------------------------------------------------------------
def exptime(skipprecond=False, skippostcond=False):
    '''Returns the exposure time per coadd in seconds.
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
    ITIMEkw = ktl.cache(service='mds', keyword='ITIME')
    ITIME = float(ITIMEkw.read()/1000)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return ITIME


##-----------------------------------------------------------------------------
## set exptime
##-----------------------------------------------------------------------------
def set_exptime(input, skipprecond=False, skippostcond=False):
    '''Set exposure time per coadd in seconds.  Note the ITIME keyword uses ms.
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
    ITIMEkw = ktl.cache(service='mds', keyword='ITIME')
    ITIMEkw.write(float(input)*1000)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return None


##-----------------------------------------------------------------------------
## coadds
##-----------------------------------------------------------------------------
def coadds(skipprecond=False, skippostcond=False):
    '''Return the number of coadds
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
    COADDSkw = ktl.cache(service='mds', keyword='COADDS')
    COADDS = int(COADDSkw.read())

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return COADDS


##-----------------------------------------------------------------------------
## set OUTDIR
##-----------------------------------------------------------------------------
def set_coadds(input, skipprecond=False, skippostcond=False):
    '''Set coadds
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
    COADDSkw = ktl.cache(service='mds', keyword='COADDS')
    COADDSkw.write(int(input))
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return None


##-----------------------------------------------------------------------------
## sampmode & numreads
##-----------------------------------------------------------------------------
def sampmode(skipprecond=False, skippostcond=False):
    '''Return the sampling mode as a string (e.g. CDS, MCDS16, etc.)
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
    SAMPMODEkw = ktl.cache(service='mds', keyword='SAMPMODE')
    NUMREADSkw = ktl.cache(service='mds', keyword='NUMREADS')
    output = {2: 'CDS', 3: 'MCDS'}.get(int(SAMPMODEkw.read()), 'UNKNOWN')
    if output == 'MCDS':
        output += NUMREADSkw.read()
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return output


##-----------------------------------------------------------------------------
## set sampmode & numreads
##-----------------------------------------------------------------------------
def set_sampmode(input, skipprecond=False, skippostcond=False):
    '''Set the sampling mode from a string (e.g. CDS, MCDS16, etc.)
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        namematch = re.match('(M?CDS)(\d*)', input.strip())
        if namematch is None:
            raise FailedCondition(f'Unable to parse "{input}"')
        mode = {'CDS': 2, 'MCDS': 3}.get(namematch.group(1))
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    SAMPMODEkw = ktl.cache(service='mds', keyword='SAMPMODE')
    NUMREADSkw = ktl.cache(service='mds', keyword='NUMREADS')
    SAMPMODEkw.write(mode)
    if mode == 3:
        nreads = int(namematch.group(2))
        NUMREADSkw.write(nreads)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        result = sampmode()
        if input != result:
            raise FailedCondition(f'Failed to set SAMPMODE and NUMREADS. "{input}" != "{result}"')

    return None


##-----------------------------------------------------------------------------
## take exposure
##-----------------------------------------------------------------------------
def take_exposure(exptime=None, coadds=None, sampmode=None, wait=True,
                  waitforFCS=True, updateFCS=True,
                  skipprecond=False, skippostcond=False):
    '''Take an exposure.
    
    If the exptime, coadds, sampmode inputs are specified, those parameters for
    the exposure will be set prior to triggering the exposure.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        waitfor_exposure()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    if exptime is not None:
        set_exptime(exptime)
    if coadds is not None:
        set_coadds(coadds)
    if sampmode is not None:
        set_sampmode(sampmode)
    if updateFCS is True:
        update_FCS()
        sleep(1)
    if waitforFCS is True:
        waitfor_FCS()
    
    GOkw = ktl.cache(service='mds', keyword='GO')
    log.info('Taking exposure')
    GOkw.write(True)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if wait is True:
            sleep(2)
            waitfor_exposure()
        imagefile = lastfile()
        if imagefile.exists():
            log.info(f'  Found last file {imagefile.name}')
        else:
            raise FailedCondition(f'Did not find file: {imagefile}')

    return None


##-------------------------------------------------------------------------
## MOSFIRE Exposure Control Functions
##-------------------------------------------------------------------------
def goi(exptime=None, coadds=None, sampmode=None, wait=True,
        waitforFCS=True, updateFCS=True,
        skipprecond=False, skippostcond=False):
    '''Alias take_exposure to goi
    '''
    take_exposure(exptime=exptime, coadds=coadds, sampmode=sampmode, wait=wait,
                  waitforFCS=waitforFCS, updateFCS=updateFCS,
                  skipprecond=skipprecond, skippostcond=skippostcond)


