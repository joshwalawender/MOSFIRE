import ktl

from .core import *

def filter1ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the filter wheel status.
    '''
    # Check filter wheel 1 status
    mmf1s_statuskw = ktl.cache(service='mmf1s', keyword='STATUS')
    filter1_status = mmf1s_statuskw.read()
    if filter1_status != 'OK':
        raise FailedPrePostCondition(f'Filter 1 status is not OK: "{filter1_status}"')


def filter2ok():
    '''Commonly used pre- and post- condition to check whether there are errors
    in the filter wheel status.
    '''
    # Check filter wheel 2 status
    mmf2s_statuskw = ktl.cache(service='mmf2s', keyword='STATUS')
    filter2_status = mmf2s_statuskw.read()
    if filter2_status != 'OK':
        raise FailedPrePostCondition(f'Filter 2 status is not OK: "{filter2_status}"')


def waitfordark(timeout=60):
    '''Commonly used pre- and post- condition to check whether the instrument is
    in a dark state.
    '''
    endat = dt.utcnow() + tdelta(seconds=timeout)
    done = isdark()
    while not done and dt.utcnow() < endat:
        sleep(1)
        done = isdark()
    if not done:
        raise FailedPrePostCondition(f'Timeout exceeded on waiting for filter to be dark')


def filter(skipprecond=False, skippostcond=False):
    '''Query for the current filter.
    
    This returns a single value which is the result of the pair of filter wheels
    in the instrument.  If you want to know the position of one filter wheel in
    particular, see filter1 and filter2 below
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            filter1ok()
            filter2ok()
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            filter1ok()
            filter2ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(skipprecond=skipprecond)

    # ----> insert instrument script here <----
    filterkw = ktl.cache(service='mosfire', keyword='FILTER')
    filter_str = filterkw.read()

    postcondition(skippostcond=skippostcond)

    return filter_str


def isdark(skipprecond=False, skippostcond=False):
    '''Return True if the current observing mode is dark
    '''
    filter_str = filter(skipprecond=skipprecond, skippostcond=skippostcond)
    return (filter_str == 'Dark')


def filter1(skipprecond=False, skippostcond=False):
    '''Query for the filter in filter wheel 1.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            filter1ok()
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            filter1ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(skipprecond=skipprecond)

    # ----> insert instrument script here <----
    filterkw = ktl.cache(service='mmf1s', keyword='POSNAME')
    filter_str = filterkw.read()

    postcondition(skippostcond=skippostcond)

    return filter_str


def filter2(skipprecond=False, skippostcond=False):
    '''Query for the filter in filter wheel 1.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            filter2ok()
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            filter2ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(skipprecond=skipprecond)

    # ----> insert instrument script here <----
    filterkw = ktl.cache(service='mmf2s', keyword='POSNAME')
    filter_str = filterkw.read()

    postcondition(skippostcond=skippostcond)

    return filter_str


def quick_dark(filter=None, wait=False, timeout=30,
               skipprecond=False, skippostcond=False):
    '''Set the instrument to a dark mode which is close to the specified filter.
    Modeled after darkeff script.
    '''
    
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    def precondition(skipprecond=False):
        '''docstring
        '''
        if skipprecond is True:
            log.debug('Skipping pre condition checks')
        else:
            pass
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    def postcondition(wait, timeout, skippostcond=False):
        '''docstring
        '''
        if skippostcond is True:
            log.debug('Skipping post condition checks')
        else:
            if wait is True:
                waitfordark(timeout=timeout)
            filter1ok()
            filter2ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    precondition(skipprecond=skipprecond)

    log.info('Setting quick dark')
    if filter not in filters and filter is not None:
        log.error(f'Filter {filter} not in allowed filter list: {filters}')
        filter = None
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
    f1dest, f2dest = filter_combo.get(filter)
    if filter1() != f1dest:
        filter1kw = ktl.cache(service='mmf1s', keyword='TARGNAME')
        filter1kw.write(f1dest)

    if filter2() != f2dest:
        filter2kw = ktl.cache(service='mmf2s', keyword='TARGNAME')
        filter2kw.write(f2dest)

    postcondition(wait, timeout, skippostcond=skippostcond)

    return None


def go_dark(filter=None, wait=False, timeout=30,
             skipprecond=False, skippostcond=False):
    '''Alias for quick_dark
    '''
    quick_dark(filter=filter, wait=wait, timeout=timeout,
               skipprecond=skipprecond, skippostcond=skippostcond)

