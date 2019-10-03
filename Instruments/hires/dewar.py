from .core import *


def is_filling():
    response = get('hiccd', 'UTBN2FIL')
    if response == 'off':
        return False
    elif response == 'on':
        return True
    else:
        log.error(f'Could not interpret UTBN2FIL: {response}')
        return None


def get_DWRN2LV():
    """Returns a float of the current camera dewar level.  Note this may
    or may not be accurately calibrated.  As of May 2019, it is reasonably
    close to 100 being full.
    """
    return get('hiccd', 'DWRN2LV', mode=float)


def estimate_dewar_time():
    """Estimate time remaining on the camera dewar.  Updated May 2019 based
    on recent calibration of dewar level sensor.
    """
    rate = 6 # 6 percent per hour
    DWRN2LV = get_DWRN2LV()
    log.info('Estimating camera dewar hold time ...')
    if DWRN2LV > 10:
        hold_time = (DWRN2LV-10)/rate
    else:
        log.warning(f'Dewar at {DWRN2LV:.1f} %. Fill immediately!')
        hold_time = 0
    hold_time_str = f"~{hold_time:.1f} hours"
    log.info(f'  hold time: {hold_time_str}')
    return hold_time


def get_RESN2LV():
    """Returns a float of the current reserve dewar level.  Each camera
    dewar fill takes roughly 10% of the reserve dewar.
    """
    return get('hiccd', 'RESN2LV', mode=float)


def fill_dewar():
    """Fill camera dewar using procedure in /local/home/hireseng/bin/filln2
    """
    log.info('Initiating dewar fill ...')
    if get_WCRATE() is not False:
        log.warning('The CCD is reading out. Try again when complete.')
        return None
    set('hiccd', 'UTBN2FIL', 'on')
    while is_filling() is True:
        DWRN2LV = get_DWRN2LV()
        RESN2LV = get_RESN2LV()
        sleep(30)
    log.info('  HIRES Dewar Fill is Complete.')
    DWRN2LV = get_DWRN2LV()
    RESN2LV = get_RESN2LV()
    log.info('  CCD Dewar: {DWRN2LV:.1f} % full')
    log.info('  Reserve Dewar: {RESN2LV:.1f} % full')
    return True
