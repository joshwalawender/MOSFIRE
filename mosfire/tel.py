from .core import *
from .magiq import get_camparms
dcs = ktl.cache(service='dcs')

##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def instrument_is_MOSFIRE():
    '''Verifies that MOSFIRE is the currently selected instrument.
    '''
    INSTRUMEkw = ktl.cache(service='dcs', keyword='INSTRUME')
    if INSTRUMEkw.read() != 'MOSFIRE':
        raise FailedCondition('MOSFIRE is not the selected instrument')


def are_we_guiding():
    '''Verifies that we are currently guiding
    '''
    return dcs['AUTACTIV'].read() == 'yes'


##-----------------------------------------------------------------------------
## Get MAGIQ Exposure Parameters
##-----------------------------------------------------------------------------
def get_camparms(skipprecond=False, skippostcond=False):
    '''Get and parse the CAMPARMS keyword.  Return a dict with the values.
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

    # CAMPARMS = mosfire,866,386,49,49,2.00,1,5,5400
    CAMPARMSkw = ktl.cache(service='magiq', keyword='CAMPARMS')
    camname, starx, stary, boxx, boxy, exptime, aa, bb, count = CAMPARMSkw.read().split(',')
    CAMPARMS = {'camname': camname,
                'stary': float(stary),
                'stary': float(stary),
                'boxx': int(boxx),
                'boxy': int(boxy),
                'exptime': float(exptime),
                'a': aa,
                'b': bb,
                'count': count,
                }

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return CAMPARMS


##-----------------------------------------------------------------------------
## wait_for_guider
##-----------------------------------------------------------------------------
def wait_for_guider(ncycles=2, timeout=20, skipprecond=False, skippostcond=False):
    '''Wait for guider to complete ncycles
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

    log.debug('Checking for guiding')
    if are_we_guiding() is False:
        return None

    # waitfor -s dcs axestat=tracking
    log.debug('Wait for tracking')
    ktl.waitfor('$dcs.AXESTAT == tracking', timeout=None)
    # get AUTRESUM value (i)
    autresum0 = dcs['AUTRESUM'].read()
    # wait until AURESUM increments (j) (timeout=20s)
    log.debug(f'Wait for AUTRESUM to increment (timeout={timeout})')
    ktl.waitfor(f'$dcs.AUTRESUM != {autresum0}', timeout=timeout)
    # wait until AUTGO is RESUMEACK or GUIDE (timeout=20s)
    log.debug('Wait for AUTGO to be guide or resumeAck')
    ktl.waitfor('($dcs.AUTGO == guide) or ($dcs.AUTGO == resumeAck)')

    camparms = get_camparms()
    waittime = ncycles*camparms['exptime']
    log.debug(f'Waiting {ncycles} guide cycles ({waittime:.1f} s)')
    sleep(waittime)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None


##-----------------------------------------------------------------------------
## mxy offset
##-----------------------------------------------------------------------------
def mxy(dx, dy, guidecycles=2, skipprecond=False, skippostcond=False):
    '''Moves dx dy arcseconds in the instrument pixel coordinates.
    
    Calls shell scripts:
    - mosfireScriptMsg
    - wftel
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        instrument_is_MOSFIRE()
        # tracking is True?
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    autresum = dcs['autresum'].read()
    angle = 0.136 * np.pi/180 # offset between CSU and detector [rad]
    u = dx*np.cos(angle) + dy*np.sin(angle)
    v = dy*np.cos(angle) - dx*np.sin(angle)

    now = datetime.utcnow()
    exec_date = now.strftime('%Y/%m/%d,%H:%M:%S')

    dcs['instxoff'].write(u)
    dcs['instyoff'].write(v)
    dcs['rel2curr'].write(True)

    # log the move. This should be temporary because it adds 0.05 sec to
    # the execution of the mxy command.
    nightpath = f'/s/nightly1/{now.year:4d}/{now.month:02d}/{now.day:02d}/'
#     offset_str = f'modify -s dcs instxoff={u:.3f} instyoff={v:.3f} rel2base=t'
    offset_str = f"dcs['instxoff'].write({u}) dcs['instyoff'].write({v}) dcs['rel2curr'].write(True)"
    mosfireScriptMsg = ['mosfireScriptMsg',
                        '-f', f'{nightpath}instrumentOffsets',
                        '-m', '{exec_date}        {offset_str}']
    subprocess.call(mosfireScriptMsg)

    tick = datetime.utcnow()
    subprocess.call(['wftel', autresum])
    tock = datetime.utcnow()
    duration = (tock-tick).total_seconds()
    log.debug(f'mxy wftel completed in {duration:.2f} sec')

    wait_for_guider(ncycles=guidecycles)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None


def mxy_with_args():
    p = argparse.ArgumentParser(description=description)
    p.add_argument('dx', type=float, help="X distance in arcsec")
    p.add_argument('dy', type=float, help="Y distance in arcsec")
    p.add_argument('guidecycles', type=int,
                   help="Number of guider cycles to wait after the move")
    args = p.parse_args()
    mxy(args.dx, args.dy, args.guidecycles)


##-----------------------------------------------------------------------------
## sltmov offset
##-----------------------------------------------------------------------------
def sltmov(distance, guidecycles=2, skipprecond=False, skippostcond=False):
    '''Move along slit
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        instrument_is_MOSFIRE()
        # tracking is True?

    ##-------------------------------------------------------------------------
    ## Script Contents

    angle = -3.74 * np.pi/180 # slit angle with respect to detector y pixels
    dx = distance * np.sin(angle)
    dy = distance * np.cos(angle)
    log.info(f'Making sltmov {distance}')
    mxy(dx, dy, guidecycles=guidecycles)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None


##-----------------------------------------------------------------------------
## gotobase
##-----------------------------------------------------------------------------
def gotobase(guidecycles=2, skipprecond=False, skippostcond=False):
    '''gotobase
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        instrument_is_MOSFIRE()
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    # modify -s dcs raoff=0 decoff=0 rel2base=true
    dcs['RAOFF'].write(0)
    dcs['DECOFF'].write(0)
    dcs['REL2BASE'].write(True)
    wait_for_guider(ncycles=guidecycles)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None


##-----------------------------------------------------------------------------
## markbase
##-----------------------------------------------------------------------------
def markbase(skipprecond=False, skippostcond=False):
    '''markbase
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        instrument_is_MOSFIRE()
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    dcs['MARK'].write(True)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None

