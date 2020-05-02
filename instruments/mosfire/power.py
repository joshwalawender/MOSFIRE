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
        default_power_levels = {'Y': 4,
                                'J': 9,
                                'H': 13.5,
                                'K': 14,
                                'on': 0,
                                'off': None,
                                'read': 'read'
                                }
        if type(power) is str:
            if power in default_power_levels.keys():
                power = default_power_levels[power]
            else:
                raise FailedCondition(f'Unable to parse power "{power}"')
        elif type(power) in [int, float]:
            if float(power) > 20 or float(power) < 0:
                raise FailedCondition(f'Unable to parse power "{power}"')
        else:
            raise FailedCondition(f'Expecting string, int, or float, got "{power}"')
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

    if power == 'read':
        # Read power and return
        flamp1 = ktl.cache(service='flat', keyword='flamp1')
        flamp2 = ktl.cache(service='flat', keyword='flamp2')
        flamp1_on = not (flamp1.read() == 'off')
        flamp2_on = not (flamp2.read() == 'off')
        return flamp1_on or flamp2_on
    else:
        # Set power level and turn both lamps on
        fpower = ktl.cache(service='flat', keyword='fpower')
        flamp = ktl.cache(service='flat', keyword='flamp')
        mosfire_flatspec = ktl.cache(service='mosfire', keyword='flatspec')

        if power in [None, 'off']:
            log.debug(f'Turning dome flat lamps off')
            flamp.write('off')
            mosfire_flatspec.write(0)
        else:
            log.debug(f'Turning dome flat lamps on at {power:.1f} power')
            fpower.write(power)
            flamp.write('on')
            mosfire_flatspec.write(1)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return None
