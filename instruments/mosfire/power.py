import inspect
from datetime import datetime, timedelta
from time import sleep

try:
    import ktl
except ModuleNotFoundError as e:
    pass

from .core import *


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------


##-----------------------------------------------------------------------------
## Control Power Strips
##-----------------------------------------------------------------------------
def power_strip(stripno, portno, onoff, skipprecond=False, skippostcond=False):
    '''Turns a power port on or off
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        if type(onoff) is str:
            if onoff.lower() not in ['on', 'off', 'read']:
                raise FailedCondition(f'State "{onoff}" not parsed')
            onoff = {'on': 1, 'off': 0, 'read': 'read'}[onoff]
        elif type(onoff) is int:
            if onoff not in [0, 1]:
                raise FailedCondition(f'State "{onoff}" not parsed')

    ##-------------------------------------------------------------------------
    ## Script Contents

    pwname = ktl.cache(keyword=f'PWNAME{portno:d}', service=f'mp{stripno:d}s')
    pwname = pwname.read()
    log.debug(f'Strip {stripno}, port {portno} is {pwname}')

    pwstat = ktl.cache(keyword=f'PWSTAT{portno:d}', service=f'mp{stripno:d}s')
    pwstat.monitor()

    if onoff in [0, 1]:
        log.debug(f'Setting mp{stripno:d}s PWSTAT{portno:d} to {onoff}')
        if int(pwstat) != onoff:
            pwstat.write(onoff)

    pwstat_str = {1: 'on', 0: 'off'}[int(pwstat)]

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if onoff in [0, 1]:
            if int(pwstat) != onoff:
                raise FailedCondition(f'{pwname} state is "{onoff}"')

    return pwstat_str


##-----------------------------------------------------------------------------
## Named scripts for each power outlet
##-----------------------------------------------------------------------------
def glycol_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 1, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def csu_controller_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 2, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def csu_drive_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 3, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def jade2_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 4, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def computer_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 5, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def lantronix_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 6, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def Ne_lamp(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 7, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def Ar_lamp(onoff, skipprecond=False, skippostcond=False):
    return power_strip(1, 8, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def guider_focus_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 1, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def varian_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 2, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def guider_camera_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 3, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def lakeshore_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 4, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def motor_box_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 5, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def power_supplies_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 6, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def fcs_controller_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 7, onoff, skipprecond=skipprecond, skippostcond=skippostcond)

def dewar_heater_power(onoff, skipprecond=False, skippostcond=False):
    return power_strip(2, 8, onoff, skipprecond=skipprecond, skippostcond=skippostcond)


##-----------------------------------------------------------------------------
## Control Dome Flat Lamps
##-----------------------------------------------------------------------------
def dome_flat_lamps(power, skipprecond=False, skippostcond=False):
    '''Turns dome flat lamps on or off
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        # Parse power input
        default_power_levels = {'Y': 4, 'J': 9, 'H': 13.5, 'K': 14,
                                'on': 0, 'off': None, 'read': 'read'}
        if type(power) is str:
            if power in default_power_levels.keys():
                power = default_power_levels[power]
            else:
                raise FailedCondition(f'Unable to parse power "{power}"')
        elif type(power) in [int, float]:
            if float(power) > 20 or float(power) < 0:
                raise FailedCondition(f'Power {power} must be between 20 (low) and 0 (high)')
        else:
            raise FailedCondition(f'Expecting str, int, or float, got {type(power)}')
        # Check that instrument is MOSFIRE
        instrument_is_MOSFIRE()

        # Hack to test code before flat service is added to MOSFIRE
        from ktl import Exceptions as ktlExceptions
        try:
            fpower = ktl.cache(service='flat', keyword='fpower')
        except ktlExceptions.ktlError as ke:
            log.error('Could not access flat keywords')
            log.error('Passing for code testing, rather than raising exception')
            log.error(f'Not attempting to set dome flat lamps to {power}')
            return None

    ##-------------------------------------------------------------------------
    ## Script Contents

    flamp1 = ktl.cache(service='dcs', keyword='flamp1')
    flamp2 = ktl.cache(service='dcs', keyword='flamp2')
    fpower = ktl.cache(service='dcs', keyword='fpower')
    fpower.monitor()

    if power == 'read':
        # Read status
        flamp1_on = not (flamp1.read() == 'off')
        flamp2_on = not (flamp2.read() == 'off')
        if flamp1_on and flamp2_on:
            flatstate = ('on', fpower)
        elif not flamp1_on and not flamp2_on:
            flatstate = ('off', fpower)
        else:
            flatstate = (f'partial: {flamp1_on} {flamp2_on}', fpower)
    else:
        # Set power level and turn both lamps on
        mosfire_flatspec = ktl.cache(service='mosfire', keyword='flatspec')

        if power in [None, 'off']:
            log.debug(f'Turning dome flat lamps off')
            flamp1.write('off')
            flamp2.write('off')
            mosfire_flatspec.write(0)
        else:
            log.debug(f'Turning dome flat lamps on at {power:.1f} power')
            fpower.write(power)
            flamp1.write('on')
            flamp2.write('on')
            mosfire_flatspec.write(1)
        flatstate = dome_flat_lamps('read', skippostcond=True)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if type(power) in [int, float]:
            if abs(fpower - power) > 0.2:
                raise FailedCondition(f'Flat lamps did not reach power: {fpower:.1f}')
        elif power is None:
            flamp1_on = not (flamp1.read() == 'off')
            flamp2_on = not (flamp2.read() == 'off')
            if flamp1_on or flamp2_on:
                raise FailedCondition(f'Flat lamps did not turn off: {flamp1_on} {flamp2_on}')

    return flatstate
