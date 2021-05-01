from .core import *


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def instrument_is_MOSFIRE():
    '''Verifies that MOSFIRE is the currently selected instrument.
    '''
    INSTRUMEkw = ktl.cache(service='dcs', keyword='INSTRUME')
    if INSTRUMEkw.read() != 'MOSFIRE':
        raise FailedCondition('MOSFIRE is not the selected instrument')


##-----------------------------------------------------------------------------
## mxy offset
##-----------------------------------------------------------------------------
def mxy(dx, dy, skipprecond=False, skippostcond=False):
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

    dcs = ktl.cache(service='dcs')

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
    print(f'mxy wftel completed in {duration:.2f} sec')
    
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
    args = p.parse_args()
    mxy(args.dx, args.dy)


##-----------------------------------------------------------------------------
## sltmov offset
##-----------------------------------------------------------------------------
def sltmov(distance, skipprecond=False, skippostcond=False):
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

    dcs = ktl.cache(service='dcs')
    angle = -3.74 * np.pi/180 # slit angle with respect to detector y pixels
    dx = distance * np.sin(angle)
    dy = distance * np.cos(angle)
    log.info(f'Making sltmov {distance}')
    mxy(dx, dy)
    
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
def gotobase(skipprecond=False, skippostcond=False):
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

    dcs = ktl.cache(service='dcs')
    # modify -s dcs raoff=0 decoff=0 rel2base=true
    dcs['RAOFF'].write(0)
    dcs['DECOFF'].write(0)
    dcs['REL2BASE'].write(True)
    
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

    dcs = ktl.cache(service='dcs')
    dcs['MARK'].write(True)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None

