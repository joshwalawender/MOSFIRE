import inspect
from datetime import datetime, timedelta
from time import sleep

from .core import *


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def filter1_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the filter wheel status.
    '''
    # Check filter wheel 1 status
    mmf1s_status = ktl.cache(service='mmf1s', keyword='STATUS')
    filter1_status = mmf1s_status.read()
    log.debug(f'Filter1 status is "{filter1_status}"')
    if filter1_status not in ['OK', 'Moving']:
        raise FailedCondition(f'Filter 1 status is not OK: "{filter1_status}"')


def filter2_ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the filter wheel status.
    '''
    # Check filter wheel 2 status
    mmf2s_status = ktl.cache(service='mmf2s', keyword='STATUS')
    filter2_status = mmf2s_status.read()
    log.debug(f'Filter2 status is "{filter2_status}"')
    if filter2_status not in ['OK', 'Moving']:
        raise FailedCondition(f'Filter 2 status is not OK: "{filter2_status}"')


##-----------------------------------------------------------------------------
## get filter
##-----------------------------------------------------------------------------
def filter(skipprecond=False, skippostcond=False):
    '''Query for the current filter.
    
    This returns a single value which is the result of the pair of filter wheels
    in the instrument.  If you want to know the position of one filter wheel in
    particular, see filter1 and filter2 below
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter1_ok()
        filter2_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    filterkw = ktl.cache(service='mosfire', keyword='FILTER')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        filter1_ok()
        filter2_ok()

    return str(filterkw.read())


##-----------------------------------------------------------------------------
## is_dark
##-----------------------------------------------------------------------------
def is_dark(skipprecond=False, skippostcond=False):
    '''Return True if the current observing mode is dark
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter1_ok()
        filter2_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    filterkw = ktl.cache(service='mosfire', keyword='FILTER')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        filter1_ok()
        filter2_ok()

    return (str(filterkw.read()) == 'Dark')


##-----------------------------------------------------------------------------
## waitfordark
##-----------------------------------------------------------------------------
def waitfordark(timeout=60, skipprecond=False, skippostcond=False):
    '''Wait for the instrument to be in a dark state.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter1_ok()
        filter2_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    endat = datetime.utcnow() + timedelta(seconds=timeout)
    filterkw = ktl.cache(service='mosfire', keyword='FILTER')

    while datetime.utcnow() < endat and str(filterkw.read()) != 'Dark':
        sleep(1)
    if str(filterkw.read()) != 'Dark':
        raise TimeoutError('Timed out waiting for instrument to be dark')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        filter1_ok()
        filter2_ok()

    return None


##-----------------------------------------------------------------------------
## filter1
##-----------------------------------------------------------------------------
def filter1(skipprecond=False, skippostcond=False):
    '''Query for the filter in filter wheel 1.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter1_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    filter1kw = ktl.cache(service='mmf1s', keyword='POSNAME')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        filter1_ok()
    
    return str(filter1kw.read())


##-----------------------------------------------------------------------------
## filter2
##-----------------------------------------------------------------------------
def filter2(skipprecond=False, skippostcond=False):
    '''Query for the filter in filter wheel 1.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter2_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    filter2kw = ktl.cache(service='mmf2s', keyword='POSNAME')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        filter2_ok()
    
    return str(filter2kw.read())


##-----------------------------------------------------------------------------
## Go Dark
##-----------------------------------------------------------------------------
def _go_dark(wait=True, timeout=30):
    '''Set the instrument to a dark mode which is close to the specified filter.
    Modeled after darkeff script.
    '''
    if is_dark():
        log.debug('Instrument is dark')
    else:
        log.debug('Setting quick dark')
        filter_combo = {'Y': ['H2', 'Y'],
                        'J': ['NB1061', 'J'],
                        'H': ['NB1061', 'H'],
                        'Ks': ['NB1061', 'Ks'],
                        'K': ['NB1061', 'K'],
                        'J2': ['J2', 'K'],
                        'J3': ['J3', 'K'],
                        'H1': ['H1', 'K'],
                        'H2': ['H2', 'K'],
                        None: ['NB1061', 'Ks'],
                        }
        f1dest, f2dest = filter_combo.get(filter())
        if filter1() != f1dest:
            f1targkw = ktl.cache(service='mmf1s', keyword='TARGNAME')
            f1targkw.write(f1dest)

        if filter2() != f2dest:
            f2targkw = ktl.cache(service='mmf2s', keyword='TARGNAME')
            f2targkw.write(f2dest)


def go_dark(wait=True, timeout=30,
            skipprecond=False, skippostcond=False):
    '''Set the instrument to a dark mode which is close to the specified filter.
    Modeled after darkeff script.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        filter1_ok()
        filter2_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    try:
        _go_dark()
    except:
        # A single retry
        _go_dark()

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if wait is True:
            waitfordark(timeout=timeout)
        filter1_ok()
        filter2_ok()

    return None


##-------------------------------------------------------------------------
## Aliases
##-------------------------------------------------------------------------
quick_dark = go_dark