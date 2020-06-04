import inspect
from datetime import datetime, timedelta
from time import sleep
import re
import numpy as np
from astropy.table import Table, Column, Row

from .core import *
from .mask import Mask
from .rotator import safe_angle


##-----------------------------------------------------------------------------
## pre- and post- conditions
##-----------------------------------------------------------------------------
def CSUbar_ok(barnum):
    '''Commonly used pre- and post- condition to check whether there are errors
    in the CSU bar status for a specified bar.
    '''
    bstatkw = ktl.cache(keyword=f"B{int(barnum):02d}STAT", service='mcsus')
    bar_status = bstatkw.read()
    if bar_status not in ['OK', 'SETUP']:
        raise FailedCondition(f'Bar {int(barnum):02d} status is {bar_status}')


def CSUbars_ok():
    '''Simple loop to check all bars in the CSU.
    '''
    log.debug('Checking CSU bars status')
    for barnum in range(1,93,1):
        CSUbar_ok(barnum)


def CSUready():
    '''Commonly used pre- and post- condition to check whether the CSU is in an
    error state.
    '''
    log.debug('Checking CSU status')
    csureadykw = ktl.cache(keyword='CSUREADY', service='mcsus')
    csuready = int(csureadykw.read())
    translation = {0: 'Unknown',
                   1: 'System Started',
                   2: 'Ready for Move',
                   3: 'Moving',
                   4: 'Configuring',
                   -1: 'Error',
                   -2: 'System Stopped'}[csuready]
    if csuready == -1:
        raise CSUFatalError()
    if csuready in [0, -2]:
        raise FailedCondition(f'CSU is not ready: {translation}')


##-----------------------------------------------------------------------------
## Setup Mask
##-----------------------------------------------------------------------------
def setup_mask(mask, wait=True, skipprecond=False, skippostcond=False):
    '''Setup the given mask.  Accepts a Mask object.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        log.debug('Verifying input')
        if type(mask) != Mask:
            raise FailedCondition(f"Input {mask} is not a Mask object")
        CSU_ok()
        CSUbars_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    log.info(f'Setting up mask: {mask.name}')
    log.debug('Setting bar target position keywords')

    mcsus = ktl.cache(service='mcsus')
    for slit in mask.slitpos:
        rbn = slit['rightBarNumber']
        rbp = slit['rightBarPositionMM']
        lbn = slit['leftBarNumber']
        lbp = slit['leftBarPositionMM']
        log.debug(f"  Setting B{rbn:02d}TARG = {rbp}")
        mcsus[f"B{rbn:02d}TARG"].write(rbp)
        log.debug(f"  Setting B{lbn:02d}TARG = {lbp}")
        mcsus[f"B{lbn:02d}TARG"].write(lbp)

    log.debug('Invoke SETUP process on CSU')
    mcsus['SETUPINIT'].write(1)
    mcsus['SETUPNAME'].write(mask.name)

    if wait is True:
        log.debug('Waiting for setup to complete')
        csustat = ktl.cache(keyword='CSUSTAT', service='mcsus')
        while str(csustat.read()) in ['Creating Group.', 'Adding bars to Group.']:
            sleep(0.5)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        log.debug('Checking for aborted setup')
        final_status = str(csustat.read())
        if re.search('Setup aborted.  Collision detected at row (\d+)', final_status):
            raise FailedCondition(final_status)
        CSU_ok()
        CSUbars_ok()
    
    return None


##-----------------------------------------------------------------------------
## execute_mask
##-----------------------------------------------------------------------------
def execute_mask(wait=True, override=False,
                 skipprecond=False, skippostcond=False):
    '''Execute a mask which has already been set up.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        CSUbars_ok()
        CSUready()
        if override is False:
            safe_angle()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    log.info('Executing mask')
    csugokw = ktl.cache(service='mcsus', keyword='SETUPGO')
    csugokw.write(1)
    sleep(3) # shim needed because CSUREADY keyword doesn't update fast enough
    if wait is True:
        waitfor_CSU(skipprecond=True)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return None


##-----------------------------------------------------------------------------
## Initialize Bars
##-----------------------------------------------------------------------------
def initialize_bars(bars, timeout=360, skipprecond=False, skippostcond=False):
    '''Initialize one or more CSU bars.
    
    To initialize all bars, use "all" as the input.  To initialize
    a single bar, use the ID number of the bar (1-92) as the input.  To
    initialize a subset of bars, use a list of bar ID numbers as the input.
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
    CSUINITBARkw = ktl.cache(keyword='INITBAR', service='mcsus')
    csureadykw = ktl.cache(keyword='CSUREADY', service='mcsus')

    if bars == 'all':
        bars = 0
    if type(bars) == int:
        bars = [bars]
    if type(bars) == list:
        for bar in bars:
            if type(bar) != int:
                raise FailedCondition(f'Bar {bar} is not integer')
            if bar < 1 or bar > 92:
                raise FailedCondition(f'Bar {bar} is not in range 1-92')

    if bars == 0:
        log.info('Initializing all bars')

    endat = datetime.utcnow() + timedelta(seconds=timeout*len(bars))
    for bar in bars:
        log.info(f'Initializing bar {bar}')
        CSUINITBARkw.write(bar)
        log.debug('Waiting for bar to finish initializing')
        while int(csureadykw.read()) != 1 and datetime.utcnow() < endat:
            if int(csureadykw.read()) == -1:
                raise CSUFatalError()
            sleep(2)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return None


##-----------------------------------------------------------------------------
## Wait For CSU
##-----------------------------------------------------------------------------
def waitfor_CSU(timeout=480, noshim=False, skipprecond=False, skippostcond=False):
    '''Wait for a CSU move to be complete.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        CSU_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    csureadykw = ktl.cache(keyword='CSUREADY', service='mcsus')

    endat = datetime.utcnow() + timedelta(seconds=timeout)
    if noshim is False:
        sleep(1)
    while int(csureadykw.read()) != 2 and datetime.utcnow() < endat:
        if int(csureadykw.read()) == -1:
            raise CSUFatalError()
        sleep(2)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        CSU_ok()
        if int(csureadykw.read()) != 2:
            raise FailedCondition('Timeout exceeded on waitfor_CSU')
    
    return None


##-----------------------------------------------------------------------------
## get_current_mask
##-----------------------------------------------------------------------------
def get_current_mask(skipprecond=False, skippostcond=False):
    '''Get the current state of the CSU from keywords and build a Mask object.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        CSU_ok()
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    mcsus = ktl.cache(service='mcsus')

    log.debug('Getting bar positions')
    barpos = [float(mcsus[f"B{bar:02d}POS"].read()) for bar in range(1,93,1)]
    log.debug('Getting bar target positions for comparison')
    bartarg = [float(mcsus[f"B{bar:02d}TARG"].read()) for bar in range(1,93,1)]
    log.debug('Verifying differences are small')
    deltas = [abs(pair[0]-pair[1]) < 0.01 for pair in zip(barpos, bartarg)]
    assert np.all(deltas)

    log.debug('Building mask object from keyword data')
    current_mask = Mask(None)
    current_mask.name = str(mcsus['MASKNAME'].read())
    slits_list = []
    for slitno in range(1,47,1):
        leftbar = slitno*2
        leftmm = barpos[leftbar-1]
        rightbar = slitno*2-1
        rightmm = barpos[rightbar-1]
        centermm = (leftmm + rightmm) / 2
        slitcent = 189.62934431020133 - 1.3801254681363402 * centermm
        width = (leftmm - rightmm)*0.7/0.507
        slits_list.append( {'centerPositionArcsec': slitcent,
                            'leftBarNumber': leftbar,
                            'leftBarPositionMM': leftmm,
                            'rightBarNumber': rightbar,
                            'rightBarPositionMM': rightmm,
                            'slitNumber': slitno,
                            'slitWidthArcsec': width,
                            'target': ''} )
    current_mask.slitpos = Table(slits_list)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        CSU_ok()

    return current_mask


##-----------------------------------------------------------------------------
## read_csu_bar_state
##-----------------------------------------------------------------------------
def read_csu_bar_state(skipprecond=False, skippostcond=False):
    '''docstring
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        if not csu_bar_state_file.exists():
            raise FailedCondition(f"Unable to locate csu_bar_state file: "
                                  f"{csu_bar_state_file}")
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    mask = Mask(None)
    mask.name = 'From csu_bar_state'
    with open(csu_bar_state_file, 'r') as cbs:
        lines = cbs.readlines()
    t = Table(names=('slitNumber', 'leftBarNumber', 'rightBarNumber',
                     'leftBarPositionMM', 'rightBarPositionMM',
                     'centerPositionArcsec', 'slitWidthArcsec', 'target'),
              dtype=('i4', 'i4', 'i4', 'f4', 'f4', 'f4', 'f4', 'a30'))
    for line in lines:
        barno, barpos, barstate = line.strip('\n').split(',')
        slit = bar_to_slit(int(barno))
        if int(barno) % 2 != 0:
            dict = {'slitNumber': slit}
            dict['leftBarNumber'] = -1
            dict['leftBarPositionMM'] = float('nan')
            dict['rightBarNumber'] = int(barno)
            dict['rightBarPositionMM'] = float(barpos)
            dict['centerPositionArcsec'] = float('nan')
            dict['slitWidthArcsec'] = float('nan')
            dict['target'] = ''
            t.add_row(dict)
        else:
            t[slit-1]['leftBarNumber'] = int(barno)
            t[slit-1]['leftBarPositionMM'] = float(barpos)
    mask.slitpos = t

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return mask


## ------------------------------------------------------------------
##  Coordinate Transformation Utilities
## ------------------------------------------------------------------
def slit_to_bars(slit):
    '''Given a slit number (1-46), return the two bar numbers associated
    with that slit.
    '''
    return (slit*2-1, slit*2)


def bar_to_slit(bar):
    '''Given a bar number, retun the slit associated with that bar.
    '''
    return int((bar+1)/2)


def pad(x):
    '''Pad array for affine transformation.
    '''
    return np.hstack([x, np.ones((x.shape[0], 1))])


def unpad(x):
    '''Unpad array for affine transformation.
    '''
    return x[:,:,:-1]


def fit_transforms(pixels, physical):
    '''Given a set of pixel coordinates (X, Y) and a set of physical
    coordinates (mm, slit), fit the affine transformations (forward and
    backward) to convert between the two coordinate systems.
    
    '''
    pixels = np.array(pixels)
    physical = np.array(physical)
    assert pixels.shape[1] == 2
    assert physical.shape[1] == 2
    assert pixels.shape[0] == physical.shape[0]

    # Pad the data with ones, so that our transformation can do translations too
    n = pixels.shape[0]
    pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
    unpad = lambda x: x[:,:-1]
    X = pad(pixels)
    Y = pad(physical)

    # Solve the least squares problem X * A = Y
    # to find our transformation matrix A
    A, res, rank, s = np.linalg.lstsq(X, Y, rcond=None)
    Ainv, res, rank, s = np.linalg.lstsq(Y, X, rcond=None)
    A[np.abs(A) < 1e-10] = 0
    Ainv[np.abs(A) < 1e-10] = 0
    Apixel_to_physical = A
    Aphysical_to_pixel = Ainv
    return Apixel_to_physical, Aphysical_to_pixel


def pixel_to_physical(x):
    '''Using the affine transformation determined by `fit_transforms`,
    convert a set of pixel coordinates (X, Y) to physical coordinates (mm,
    slit).
    '''
    x = np.array(x)
    Apixel_to_physical = np.array(transforms['Apixel_to_physical'])
    result = unpad(np.dot(pad(x), Apixel_to_physical))
    return result


def physical_to_pixel(x):
    '''Using the affine transformation determined by `fit_transforms`,
    convert a set of physical coordinates (mm, slit) to pixel coordinates
    (X, Y).
    '''
    x = np.array(x)
    Aphysical_to_pixel = np.array(transforms['Aphysical_to_pixel'])
    result = unpad(np.dot(pad(x), Aphysical_to_pixel))
    return result


##-----------------------------------------------------------------------------
## Aliases
##-----------------------------------------------------------------------------
CSU_ok = CSUready
