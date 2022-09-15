from .core import *


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def are_we_guiding():
    '''Verifies that we are currently guiding
    '''
    raise NotImplementedError

##-----------------------------------------------------------------------------
## Get Exposure Parameters
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
        if CAMPARMS['camname'] != 'MOSFIRE':
            raise FailedCondition(f"MOSFIRE is not the current guider ({CAMPARMS['camname']})")

    return CAMPARMS
