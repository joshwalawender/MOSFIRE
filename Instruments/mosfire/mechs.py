from .core import *

##-------------------------------------------------------------------------
## MOSFIRE Mode and Filter Functions
##-------------------------------------------------------------------------
def obsmode():
    '''Get the observing mode and return a two element list: [filter, mode]
    '''
    obsmode = get('OBSMODE')
    return obsmode


def set_obsmode(obsmode, wait=True, timeout=60):
    '''Set the current observing mode to the filter and mode specified.
    '''
    filter, mode = obsmode.split('-')
    mode = mode.lower()
    log.info(f"Setting mode to {obsmode}")
    if not mode in modes:
        log.error(f"Mode: {mode} is unknown")
    elif not filter in filters:
        log.error(f"Filter: {filter} is unknown")
    else:
        set('SETOBSMODE', obsmode, wait=True)
        if wait is True:
            endat = dt.utcnow() + tdelta(seconds=timeout)
            done = (obsmode().lower() == obsmode.lower())
            while not done and dt.utcnow() < endat:
                sleep(1)
                done = (obsmode().lower() == obsmode.lower())
            if not done:
                log.warning(f'Timeout exceeded on waiting for mode {modestr}')


def filter():
    '''Return the current filter name
    '''
    filter = get('FILTER')
    return filter


def filter1():
    '''Return the current filter name for filter wheel 1
    '''
    return get('posname', service='mmf1s')


def filter2():
    '''Return the current filter name for filter wheel 2
    '''
    return get('posname', service='mmf2s')


def is_dark():
    '''Return True if the current observing mode is dark
    '''
    filter = filter()
    return filter == 'Dark'


def quick_dark(filter=None):
    '''Set the instrument to a dark mode which is close to the specified filter.
    Modeled after darkeff script.
    '''
    log.info('Setting quick dark')
    if filter not in filters:
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
        set('targname', f1dest, service='mmf1s')
    if filter2() != f2dest:
        set('targname', f2dest, service='mmf2s')


def go_dark(filter=None, wait=True):
    '''Alias for quick_dark
    '''
    quick_dark(filter=filter)
    if wait is True:
        waitfor_dark()


def waitfor_dark(timeout=300, noshim=False):
    log.debug('Waiting for dark')
    endat = dt.utcnow() + tdelta(seconds=timeout)
    if noshim is False:
        sleep(1)
    while is_dark() is False and dt.utcnow() < endat:
        sleep(1)
    if is_dark() is False:
        log.warning(f'Timeout exceeded on waitfor_dark to finish')
    return is_dark()


##-------------------------------------------------------------------------
## MOSFIRE Status Check Functions
##-------------------------------------------------------------------------
def grating_shim_ok():
    return get('MGSSTAT') == 'OK'


def grating_turret_ok():
    return get('MGTSTAT') == 'OK'


def grating_ok():
    return get('GRATSTAT') == 'OK'


def filter1_ok():
    return get('MF1STAT') == 'OK'


def filter2_ok():
    return get('MF2STAT') == 'OK'


def filters_ok():
    return get('FILTSTAT') == 'OK'


def fcs_ok():
    return get('FCSSTAT') == 'OK'


def pupil_rotator_ok():
    return get('MPRSTAT') in ['OK', 'Tracking']


def trapdoor_ok():
    return dustcover_ok()


def dustcover_ok():
    return get('MDCSTAT') == 'OK'


def check_mechanisms():
    log.info('Checking mechanisms')
    mechs = ['filter1', 'filter2', 'fcs', 'grating_shim', 'grating_turret',
             'pupil_rotator', 'trapdoor']
    for mech in mechs:
        statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
        ok = statusfn()
        if ok is False:
            log.error(f'{mech} status is not ok')
            log.error(f'Please address the problem, then re-run the checkout.')
            return False
    return True
