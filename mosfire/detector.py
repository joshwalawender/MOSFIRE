import re

from .core import *
from .metadata import lastfile, set_object
from .fcs import update_FCS, waitfor_FCS


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def waitfor_exposure(timeout=240, shim=False):
    '''Block and wait for the current exposure to be complete.
    '''
    log.debug('Waiting for exposure to finish')
    endat = datetime.utcnow() + timedelta(seconds=timeout)
    if shim is True:
        sleep(1)
    IMAGEDONEkw = ktl.cache(service='mds', keyword='IMAGEDONE')
    READYkw = ktl.cache(service='mds', keyword='READY')

    imagedone = bool(int(IMAGEDONEkw.read()))
    mdsready = bool(int(READYkw.read()))
    done_and_ready = imagedone and mdsready
    while datetime.utcnow() < endat and not done_and_ready:
        sleep(0.5)
        imagedone = bool(int(IMAGEDONEkw.read()))
        mdsready = bool(int(READYkw.read()))
        done_and_ready = imagedone and mdsready
    if not done_and_ready:
        raise FailedCondition('Timeout exceeded on waitfor_exposure to finish')


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
    ITIME = float(ITIMEkw.read())/1000

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return ITIME


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
    new_exptime = float(input)*1000
    log.debug(f'Setting exposure time to {new_exptime:.1f} ms')
    ITIMEkw.write(new_exptime)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        ITIME = float(ITIMEkw.read())/1000
        log.debug(f'Exposure time is now {ITIME:.1f} sec')
    
    return None


def exptime_with_args():
    description = '''Set or view the exposure time in seconds
    '''
    p = argparse.ArgumentParser(description=description)
    p.add_argument('exptime', type=float, default=0,
                   help="The exposure time (sec)")
    args = p.parse_args()
    if args.exptime != 0.0:
        set_exptime(args.exptime)
    print(f"Exposure Time = {exptime():.1f}")


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
    log.debug(f'Setting coadds to {int(input)}')
    COADDSkw.write(int(input))
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        nCOADDS = int(COADDSkw.read())
        log.debug(f'Number of coadds is now {nCOADDS}')
        if nCOADDS != int(input):
            raise FailedCondition('Failed to set COADDS')
    
    return None


def coadds_with_args():
    description = '''Set or view the number of coadds
    '''
    p = argparse.ArgumentParser(description=description)
    p.add_argument('coadds', type=int, default=0,
                   help="The number of coadds")
    args = p.parse_args()
    if args.coadds != 0:
        set_coadds(args.coadds)
    print(f"Coadds = {coadds():d}")


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


def sampmode_with_args():
    description = '''Set or view the sampling mode
    '''
    p = argparse.ArgumentParser(description=description)
    p.add_argument('sampmode', type=str, default='',
                   help="The sampling mode (CDS or MCDS[1-16])")
    args = p.parse_args()
    if args.sampmode != '':
        set_sampmode(args.sampmode)
    print(f"Sampling Mode = {sampmode()}")



##-----------------------------------------------------------------------------
## take exposure
##-----------------------------------------------------------------------------
def take_exposure(exptime=None, coadds=None, sampmode=None, object=None,
                  wait=True, waitforFCS=False, updateFCS=False,
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
    if object is not None:
        set_object(object)
    if updateFCS is True:
        update_FCS()
        sleep(1)
    if waitforFCS is True:
        waitfor_FCS()
    
    GOkw = ktl.cache(service='mds', keyword='GO')
    log.info('Starting exposure')
    GOkw.write(True)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if wait is True:
            waitfor_exposure(shim=True)
        imagefile = lastfile()
        if imagefile.exists():
            log.info(f'  Found last file {imagefile.name}')
        else:
            raise FailedCondition(f'Did not find file: {imagefile}')

    return None


##-------------------------------------------------------------------------
## Aliases
##-------------------------------------------------------------------------
wfgo = waitfor_exposure
goi = take_exposure
