from .core import *


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
        # Check that instrument is MOSFIRE
        instrument_is_MOSFIRE()

    ##-------------------------------------------------------------------------
    ## Script Contents

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

    flamp1 = ktl.cache(service='dcs', keyword='flamp1')
    flamp2 = ktl.cache(service='dcs', keyword='flamp2')
    fpower = ktl.cache(service='dcs', keyword='fpower')

    if power == 'read':
        # Read status
        flamp1_on = not (flamp1.read() == 'off')
        flamp2_on = not (flamp2.read() == 'off')
        if flamp1_on and flamp2_on:
            flatstate = ('on', float(fpower.read()))
        elif not flamp1_on and not flamp2_on:
            flatstate = ('off', float(fpower.read()))
        else:
            flatstate = (f'partial: {flamp1_on} {flamp2_on}', float(fpower.read()))
    else:
        # Set power level and turn both lamps on
        mosfire_flatspec = ktl.cache(service='mosfire', keyword='flatspec')

        if power in [None, 'off']:
            log.info(f'Turning dome flat lamps off')
            flamp1.write('off')
            flamp2.write('off')
            mosfire_flatspec.write(0)
        else:
            log.info(f'Turning dome flat lamps on at {power:.1f} power')
            fpower.write(power)
            flamp1.write('on')
            flamp2.write('on')
            mosfire_flatspec.write(1)
        flatstate = dome_flat_lamps('read', skipprecond=skipprecond, skippostcond=True)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if type(power) in [int, float]:
            if abs(float(fpower.read()) - power) > 0.2:
                raise FailedCondition(f'Flat lamps did not reach power: {fpower.read():.1f}')
        elif power is None:
            flamp1_on = not (flamp1.read() == 'off')
            flamp2_on = not (flamp2.read() == 'off')
            if flamp1_on or flamp2_on:
                raise FailedCondition(f'Flat lamps did not turn off: {flamp1_on} {flamp2_on}')

    return flatstate
