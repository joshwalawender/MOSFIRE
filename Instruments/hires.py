#!/usr/env/python

## Import General Tools
from pathlib import Path
import argparse
import logging
import re
from datetime import datetime as dt
from time import sleep
import numpy as np
import subprocess


##-------------------------------------------------------------------------
## HIRES Properties
##-------------------------------------------------------------------------
name = 'HIRES'
# scripts = ["stare", "slit nod", "ABBA", "ABB'A'"]
binnings = ["1x1", "1x2", "2x1", "2x2", "3x1"]
lampnames = ['none', 'ThAr1', 'ThAr2', 'quartz1', 'quartz2']
serviceNames = ["hires", "hiccd", "expo"]
obstypes = ['Object', 'Dark', 'Line', 'Bias', 'IntFlat', 'DmFlat', 'SkyFlat']
slits = {'B1': (3.5, 0.574),
         'B2': (7.0, 0.574),
         'B3': (14.0, 0.574),
         'B4': (28.0, 0.574),
         'B5': (3.5, 0.861),
         'C1': (7.0, 0.861),
         'C2': (14.0, 0.861),
         'C3': (28.0, 0.861),
         'C4': (3.5, 1.148),
         'C5': (7.0, 1.148),
         'D1': (14.0, 1.148),
         'D2': (28.0, 1.148),
         'D3': (7.0, 1.722),
         'D4': (14.0, 1.722),
         'D5': (0.119, 0.179),
         'E1': (1.0, 0.4),
         'E2': (3.0, 0.4),
         'E3': (5.0, 0.4),
         'E4': (7.0, 0.4),
         'E5': (1.0, 0.8),
         }


##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description="""
""")
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
p.add_argument("-n", "--noactions", dest="noactions",
    default=False, action="store_true",
    help="Run in test mode with no instrument control.")
args = p.parse_args()


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('HIRES')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
LogConsoleHandler.setLevel(logging.DEBUG)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
# LogFileName = None
# LogFileHandler = logging.FileHandler(LogFileName)
# LogFileHandler.setLevel(logging.DEBUG)
# LogFileHandler.setFormatter(LogFormat)
# log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## Import KTL python
##-------------------------------------------------------------------------
# Wrap ktl import in try/except so that we can maintain test case or
# simulator version of functions on machines without KTL installed.
if args.noactions is True:
    ktl = None
else:
    try:
        import ktl
    except ModuleNotFoundError:
        ktl = None


# Connect to KTL Services
services = {}
if ktl is not None:
    for service in serviceNames:
        try:
            services[service] = ktl.Service(service)
        except ktl.Exceptions.ktlError:
            log.error(f"Failed to connect to service {service}")

assert len(serviceNames) == len(services.keys())


##-------------------------------------------------------------------------
## HIRES Functions
##-------------------------------------------------------------------------
def get(service, keyword, mode=str):
    """Generic function to get a keyword value.  Converts it to the specified
    mode and does some simple parsing of true and false strings.
    """
    log.debug(f'Querying {service} for {keyword}')
    if services == {}:
        return None
    assert mode in [str, float, int, bool]
    kwresult = services[service][keyword].read()
    log.debug(f'  Got result: "{kwresult}"')

    # Handle string versions of true and false
    if mode is bool:
        if kwresult.strip().lower() == 'false':
            result = False
        elif kwresult.strip().lower() == 'true':
            result = True
        log.debug(f'  Parsed to boolean: {result}')
        return result
    # Convert result to requested type
    try:
        result = mode(kwresult)
        log.debug(f'  Parsed to {mode}: {result}')
        return result
    except ValueError:
        log.warning(f'Failed to parse {kwresult} as {mode}, returning string')
        return kwresult


def set(service, keyword, value, wait=True):
    """Generic function to set a keyword value.
    """
    log.debug(f'Setting {service}.{keyword} to "{value}" (wait={wait})')
    if services == {}:
        return None
    services[service][keyword].write(value, wait=wait)
    log.debug(f'  Done.')


def get_collimator():
    """Determine which collimator is in the beam.  Returns a string of
    'red' or 'blue' indicating which is in beam.  Returns None if it can
    not interpret the result.
    """
    log.info('Getting current collimator ...')
    collred = get('hires', 'COLLRED')
    collblue = get('hires', 'COLLBLUE')
    if collred == 'red' and collblue == 'not blue':
        collimator = 'red'
    elif collred == 'not red' and collblue == 'blue':
        collimator = 'blue'
    else:
        collimator = None
    log.info(f'  collimator = {collimator}')
    return collimator


def lights_are_on():
    """Returns True if lights are on in the enclosure.
    """
    log.info('Getting status of enclosure lights ...')
    lights_str = get('hires', 'lights')
    log.info(f'  lights are {lights_str}')
    lights = (lights_str == 'on')
    return lights


def get_iodine_temps():
    """Returns the iodine cell temperatures (tempiod1, tempiod2) in units
    of degrees C.
    """
    tempiod1 = get('hires', 'tempiod1', mode=float)
    tempiod2 = get('hires', 'tempiod2', mode=float)
    return [tempiod1, tempiod2]


def check_iodine_temps(target1=65, target2=50, range=0.1, wait=False):
    """Checks the iodine cell temperatures agains the given targets and
    range.  Default values are those used by the CPS team.
    """
    log.info('Checking whether iodine cell is at operating temp ...')
    tempiod1, tempiod2 = get_iodine_temps()
    tempiod1_diff = tempiod1 - target1
    tempiod2_diff = tempiod2 - target2
    log.debug(f'  tempiod1 is {tempiod1_diff:.1f} off nominal')
    log.debug(f'  tempiod2 is {tempiod2_diff:.1f} off nominal')
    if abs(tempiod1_diff) < range and abs(tempiod2_diff) < range:
        log.info('  Iodine temperatures in range')
        return True
    else:
        log.info('  Iodine temperatures NOT in range')
        if wait is True:
            log.info('  Waiting 10 minutes for iodine cell to reach '
                          'temperature')
            done = ktl.waitFor(f'($hires.TEMPIOD1 > {target1-range}) and '\
                               f'($hires.TEMPIOD1 < {target1+range}) and '\
                               f'($hires.TEMPIOD2 > {target2-range}) and '\
                               f'($hires.TEMPIOD2 < {target2+range})',\
                               timeout=600)
            if done is False:
                logger.warning('Iodine cell did not reach temperature'
                                    'within 10 minutes')
            return done
        else:
            return False


def get_binning():
    """Return the binning value, a tuple of (binX, binY).
    """
    binningkwstr = get('hiccd', 'BINNING')
    binningmatch = re.match('\\n\\tXbinning (\d)\\n\\tYbinning (\d)',
                            binningkwstr)
    if binningmatch is not None:
        binning = (int(binningmatch.group(1)), int(binningmatch.group(2)))
        log.debug(f'binning = {binning}')
        return binning
    else:
        log.error(f'Could not parse keyword value "{binningkwstr}"')
        return None


def get_windowing():
    """Return the windowing status.
    """
    keywordresult = get('hiccd', 'WINDOW')
    winmatch = re.match('\\n\\tchip number (\d)\\n\\txstart (\d+)\\n\\t'
                        'ystart (\d+)\\n\\txlen (\d+)\\n\\tylen (\d+)',
                            keywordresult)
    if winmatch is not None:
        window = (int(winmatch.group(1)),
                  int(winmatch.group(2)),
                  int(winmatch.group(3)),
                  int(winmatch.group(4)),
                  int(winmatch.group(5)),
                 )
        log.debug(f'window = {window}')
        return window
    else:
        log.error(f'Could not parse keyword value "{keywordresult}"')
        return None


def get_gain():
    """Return the gain as a string 'low' or 'high'.
    """
    return get('hiccd', 'CCDGAIN')


def get_ccdspeed():
    """Return the CCD readout speed as a string.
    """
    return get('hiccd', 'CCDSPEED')


def set_binning(input):
    if type(input) is str:
        try:
            binX, binY = input.lower().split('x')
            binX = int(binX)
            binY = int(binY)
        except AttributeError:
            log.warning(f"Could not interpret {input} as a binning setting.")
    elif type(input) in [list, tuple]:
        try:
            binX, binY = input
        except TypeError:
            log.warning(f"Could not interpret {input} as a binning setting.")
    else:
        log.warning(f"Could not interpret {type(input)} {input} as a binning.")

    if f"{binX:d}x{binY:d}" in binnings:
        log.info(f'Setting binning to {(binX, binY)}')
        set('hiccd', 'binning', (binX, binY))
    else:
        log.error(f"{binX:d}x{binY:d} is not an available binning")
        log.error(f"  Available binnings: {binnings}")


def set_itime(itime):
    set('hiccd', 'TTIME', itime)


def is_writing():
    return get('hiccd', 'WCRATE', mode=bool)


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


def set_covers(dest, wait=True):
    """Opens or closes all internal covers.
    
    Use same process as: /local/home/hires/bin/open.red and open.blue

    modify -s hires rcocover = open \
                    echcover = open   xdcover  = open \
                    co1cover = open   co2cover = open \
                    camcover = open   darkslid = open     wait

    modify -s hires bcocover = open \
                    echcover = open   xdcover  = open \
                    co1cover = open   co2cover = open \
                    camcover = open   darkslid = open     wait
    """
    assert dest in ['open', 'closed']
    collimator = get_collimator()
    log.info(f'Setting {collimator} covers to {dest}')

    if collimator == 'red':
        set('hires', 'rcocover', dest, wait=False)
    elif collimator == 'blue':
        set('hires', 'bcocover', dest, wait=False)
    else:
        log.error('Collimator is unknown. Cover not opened.')
    set('hires', 'echcover', dest, wait=False)
    set('hires', 'co1cover', dest, wait=False)
    set('hires', 'xdcover', dest, wait=False)
    set('hires', 'co2cover', dest, wait=False)
    set('hires', 'camcover', dest, wait=False)
    set('hires', 'darkslid', dest, wait=False)

    if wait is True:
        if collimator == 'red':
            set('hires', 'rcocover', dest, wait=True)
        elif collimator == 'blue':
            set('hires', 'bcocover', dest, wait=True)
        else:
            log.error('Collimator is unknown. Cover not opened.')
        set('hires', 'echcover', dest, wait=True)
        set('hires', 'co1cover', dest, wait=True)
        set('hires', 'xdcover', dest, wait=True)
        set('hires', 'co2cover', dest, wait=True)
        set('hires', 'camcover', dest, wait=True)
        set('hires', 'darkslid', dest, wait=True)
        log.info('  Done.')


def open_covers(wait=True):
    set_covers('open', wait=wait)


def close_covers(wait=True):
    set_covers('closed', wait=wait)


def iodine_start():
    """Starts the iodine cell heater.  Cell takes ~45 minutes to warm up.
    
    Use same process as in /local/home/hires/bin/iod_start

    modify -s hires moniodt=1
    modify -s hires setiodt=50.
    modify -s hires iodheat=on
    """
    log.info('Starting iodine heater')
    set('hires', 'moniodt', 1)
    set('hires', 'setiodt', 50)
    set('hires', 'iodheat', 'on')


def iodine_stop():
    """Turns off the iodine cell heater.
    
    Use same process as in /local/home/hires/bin/iod_stop

    modify -s hires moniodt=0
    modify -s hires iodheat=off
    """
    log.info('Stopping iodine heater')
    set('hires', 'moniodt', 0)
    set('hires', 'iodheat', 'off')


def iodine_in(wait=True):
    log.info('Inserting iodine cell')
    set('hires', 'IODCELL', 'in', wait=wait)


def iodine_out(wait=True):
    log.info('Removing iodine cell')
    set('hires', 'IODCELL', 'out', wait=wait)


def open_slit(wait=True):
    """Open the slit jaws.
    """
    set('hires', 'slitname', 'opened', wait=wait)


def set_decker(deckname, wait=True):
    """Set the deckname keyword.  This method does not change any other
    configuration values.
    """
    assert deckname in slits.keys()
    slitdims = slits[deckname]
    log.info(f'Setting decker to {deckname} ({slitdims[0]} x {slitdims[1]})')
    set('hires', 'deckname', deckname, wait=wait)


def set_slit(deckname, wait=True):
    set_decker(deckname, wait=wait)


def set_filters(fil1name, fil2name, wait=True):
    """Set the filter wheels.
    """
    log.info(f'Setting filters to {fil1name}, {fil2name}')
    set('hires', 'fil1name', fil1name, wait=wait)
    set('hires', 'fil2name', fil2name, wait=wait)


def get_xdang():
    return get('hires', 'XDANGL', mode=float)


def get_xdraw():
    return get('hires', 'XDRAW', mode=int)


def set_xdang(dest, simple=False, threshold=0.5, step=0.5):
    log.info(f'Moving XDANGL to {dest:.3f} deg')
    if simple is True:
        log.debug(f"Making simple move to {dest:.3f}")
        set('hires', 'XDANGL', dest, wait=True)
    else:
        delta = dest - get_xdang()
        log.debug(f'Total move is {delta:.3f} deg')
        if abs(delta) > threshold:
            nsteps = int(np.floor(abs(delta) / step))
            log.debug(f"Will move in {nsteps+1} steps")
            for i in range(nsteps):
                movedest = get_xdang() + np.sign(delta)*step
                log.debug(f"Making intermediate move to {movedest:.3f}")
                set('hires', 'XDANGL', movedest, wait=True)
                sleep(1)
        log.debug(f"Making final move to {dest:.3f}")
        set('hires', 'XDANGL', dest, wait=True)
    XDANG = get_xdang()
    log.info(f"Done.  XDANGL = {XDANG:.3f} deg")
    return XDANG


def set_raw_xdang(dest, simple=False, threshold=2000, step=2000):
    log.info(f'Moving XDRAW to {dest:.3f} counts')
    if simple is True:
        log.debug(f"Making simple move to {dest:.3f}")
        set('hires', 'XDRAW', dest, wait=True)
    else:
        delta = dest - get_raw_xdang()
        log.debug(f'Total move is {delta:.3f} counts')
        if abs(delta) > threshold:
            nsteps = int(np.floor(abs(delta) / step))
            log.debug(f"Will move in {nsteps+1} steps")
            for i in range(nsteps):
                movedest = get_raw_xdang() + np.sign(delta)*step
                log.debug(f"Making intermediate move to {movedest:.3f}")
                set('hires', 'XDRAW', movedest, wait=True)
                sleep(1)
        log.debug(f"Making final move to {dest:.3f}")
        set('hires', 'XDRAW', dest, wait=True)
    XDRAW = get_xdraw()
    log.debug(f"Done.  XDRAW = {XDRAW:.3f} steps")
    return XDRAW


def set_cafraw(cafraw, wait=True):
    log.info(f'Setting CAFRAW to {cafraw:.3f}')
    set('hires', 'cafraw', cafraw, wait=wait)


def set_cofraw(cofraw, wait=True):
    log.info(f'Setting COFRAW to {cofraw:.3f}')
    set('hires', 'cofraw', cofraw, wait=wait)


def set_tvfilter(tvf1name, wait=True):
    log.info(f'Setting TVF1NAME to {tvf1name:.3f}')
    set('hires', 'TVF1NAME', tvf1name, wait=wait)


def get_obstype():
    obstype = get('hiccd', 'obstype')
    assert obstype in obstypes
    return obstype


def set_obstype(obstype):
    log.info(f'Setting OBSTYPE to {obstype:.3f}')
    if obstype in obstypes:
        set('hiccd', 'obstype', obstype)
        return get_obstype()
    else:
        log.error(f'OBSTYPE {obstype} not recognized.')
        log.error(f'Allowed obstypes:')
        for otype in obstypes:
            log.error(f'  {otype}')


def wait_for_observip(timeout=300):
    log.info('Waiting up to {timeout} seconds for observation to finish')
    if not ktl.waitFor('($hiccd.OBSERVIP == False )', timeout=300):
        raise Exception('Timed out waiting for OBSERVIP')


def take_exposure(obstype=None, exptime=None, nexp=1):
    """Takes one or more exposures of the given exposure time and type.
    Modeled after goi script.
    """
    obstype = get_obstype()
    if obstype.lower() not in obstypes:
        log.warning(f'OBSTYPE "{obstype} not understood"')
        return None

    wait_for_observip()

    if exptime is not None:
        set_itime(int(exptime))

    if obstype.lower() in ["dark", "bias", "zero"]:
        set('hiccd', 'AUTOSHUT', False)
    else:
        set('hiccd', 'AUTOSHUT', True)

    for i in range(nexp):
        exptime = get('hiccd', 'TTIME', mode=int)
        log.info(f"Taking exposure {i:d} of {nexp:d}")
        log.info(f"  Exposure Time = {exptime:d} s")
        set('hiccd', 'EXPOSE', True)
        exposing = ktl.Expression("($hiccd.OBSERVIP == True) "
                                  "and ($hiccd.EXPOSIP == True )")
        reading = ktl.Expression("($hiccd.OBSERVIP == True) "
                                 "and ($hiccd.WCRATE == True )")
        obsdone = ktl.Expression("($hiccd.OBSERVIP == False)")

        if not exposing.wait(timeout=30):
            raise Exception('Timed out waiting for EXPOSING to start')
        log.info('  Exposing ...')

        if not reading.wait(timeout=exptime+30):
            raise Exception('Timed out waiting for READING to start')
        log.info('  Reading out ...')

        if not obsdone.wait(timeout=90):
            raise Exception('Timed out waiting for READING to finish')
        log.info('Done')

def goi(obstype=None, exptime=None, nexp=1):
    take_exposure(obstype=obstype, exptime=exptime, nexp=nexp)


def last_file():
    OUTDIR = get('hiccd', 'OUTDIR')
    OUTFILE = get('hiccd', 'OUTFILE')
    LFRAMENO = get('hiccd', 'LFRAMENO', mode=int)
    lastfile = Path(OUTDIR).joinpath(f"{OUTFILE}{LFRAMENO:04d}.fits")
    return lastfile


def get_expo_status():
    return get('expo', 'EXM0STA')


def expo_on():
    log.info('Turning exposure meter on')
    set('expo', 'EXM0MOD', 'On')


def expo_off(self):
    log.info('Turning exposure meter off')
    set('expo', 'EXM0MOD', 'Off')


def get_lamp():
    return get('hires', 'LAMPNAME')


def set_lamp(lampname, wait=True):
    if lampname not in lampnames:
        log.error(f"{lampname} not known")
        log.error(f"Available lamps: {lampnames}")
    log.info(f'Setting lamp to {lampname}')
    set('hires', 'LAMPNAME', lampname, wait=wait)
    assert get_lamp() == lampname


def get_lamp_filter(self):
    lfilname = get('hires', 'LFILNAME')


def set_lamp_filter(self, lfilname, wait=True):
    assert lfilname in ['bg12', 'bg13', 'bg14', 'bg38', 'clear', 'dt',
                        'etalon', 'gg495', 'ng3', 'ug1', 'ug5']
    set('hires', 'LFILNAME', lfilname, wait=wait)
    assert get_lamp_name() == lfilname


# -----------------------------------------------------------------------------
# Afternoon Setup for PRV
# -----------------------------------------------------------------------------
def PRV_afternoon_setup(check_iodine=True, fnroot=None):
    """Configure the instrument for afternoon setup (PRV mode).
    """
    # Check that lights are off in the HIRES enclosure
    if lights_are_on() is True:
        print('WARNING:  Lights in HIRES enclosure are on!')
        print('WARNING:  Enclosure may be occupied, halting script.')
        return False
    # Check dewar level, if below threshold, fill
    if get_DWRN2LV() < 30:
        print(f'Dewar level at {getDWRN2LV():.1f} %. Initiating dewar fill.')
        fill_dewar()
    # Start iodine cell
    iodine_start()
    # Open covers
    open_covers()
    # Set filename root
    now = dt.utcnow()
    if fnroot is None:
        fnroot = now.strftime('%Y%m%d_')
    set('hiccd', 'OUTFILE', fnroot)
    # Set binning to 3x1
    set_binning('3x1')
    # --> Set full frame (not possible?)
    # Confirm gain=low
    assert get_gain() == 'low'
    # Confirm Speed = fast
    assert get_speed() == 'fast'
    # m slitname=opened
    open_slit()
    # m fil1name=clear
    # m fil2name=clear
    set_filters('clear', 'clear')
    # Confirm collimator = red
    assert get_collimator() == 'red'
    # m cofraw = +70000
    set_cofraw(70000)
    # m cafraw=0
    set_cafraw(0)
    # --> set ECHANG
#     set('hires', 'ECHANG', 0, wait=True)
    # --> set XDANG
#     set('hires', 'XDANG', 0, wait=True)
    # --> tvfilter to BG38
    set_tvfilter('bg38')  # check that tvfocus is set properly
    # Confirm tempiod1 and tempiod2
    if check_iodine is True:
        while check_iodine_temps() is not True:
            print('Iodine cell not at temperature.')
            tempiod1, tempiod2 = get_iodine_temps()
            print(f'  tempiod1 = {tempiod1:.1f} C')
            print(f'  tempiod2 = {tempiod2:.1f} C')
            print(f'  waiting 5 minutes before checking again (or CTRL-c to exit)')
            sleep(300)
    if check_iodine_temps() is True:
        print('Iodine cell at temperature:')
    else:
        print('Iodine cell is not at recommended temperature:')
        tempiod1, tempiod2 = get_iodine_temps()
        print(f'  tempiod1 = {tempiod1:.1f} C')
        print(f'  tempiod2 = {tempiod2:.1f} C')

    # Obstype = object
    set_obstype('Object')

    # Focus
    # - Exposure meter off
    expo_off()
    # - ThAr2 on
    set_lamp('ThAr2')
    # - Lamp filter=ng3
    set_lamp_filter('ng3')
    # - m deckname=D5
    set_decker('D5')
    # - iodine out
    iodine_out()
    # - texp = 10 seconds
    set_itime(10)
    # - expose
    take_exposure(n=1)
    
    # - -> run IDL focus routine and iterate as needed
    foc_instructions = f"""
You must now accurately position the echelle and cross disperser angles to
place particular arc lines on particular destination pixels.  This is done via
an IDL routine written by the CPS team. This routine will launch momentarily in
a new xterm.

Begin by calling the foc script on your first file:
    IDL> foc, /plt, inpfile='{lastfile}'
When a new image is called for by the foc script, just use the HIRES dashboard
GUI to take a new image.

After a new image is taken, analyze it by calling the script again using:
    IDL> foc, /plt, inpfile='[insert path to new file here]'
If you would like more details on the IDL foc routine, you can view the code
and docstring on github: 
https://github.com/Caltech-IPAC/hires-pipeline/blob/master/focus/foc.pro
For additional instructions, see: 
https://caltech-ipac.github.io/hiresprv/setup.html#spectrograph-alignment-and-focus
"""
    print(foc_instructions)
    subprocess.call(['/home/hireseng/bin/focusPRV'])


# -----------------------------------------------------------------------------
# PRV Calibrations
# -----------------------------------------------------------------------------
def PRV_calibrations():
    print('Running PRV afternoon calibrations.  Before running this, the '
          'instrument should already be configured for PRV observations.')
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        print('Exiting calibrations script.')
        return False

    # Check that lights are off in the HIRES enclosure
    if lights_are_on() is True:
        print('WARNING:  Lights in HIRES enclosure are on!')
        print('WARNING:  Enclosure may be occupied, halting script.')
        return False
    # Check dewar level, if below threshold, fill
    if get_DWRN2LV() < 30:
        print(f'Dewar level at {getDWRN2LV():.1f} %. Initiating dewar fill.')
        fill_dewar()

    # THORIUM Exposures w/ B5
    # - Exposure meter off
    expo_off()
    # - ThAr2 on
    set_lamp('ThAr2')
    # - lamp filter = ng3
    set_lamp_filter('ng3')
    # - m deckname=B5
    set_decker('B5')
    # - iodine out
    iodine_out()
    # - texp=1 second
    set_itime(1)
    # - two exposures
    take_exposure(n=2)

    # THORIUM Exposure w/ B1
    # - Exposure meter off
    # - ThAr2 on
    # - lamp filter = ng3
    # - m deckname=B1
    set_decker('B1')
    # - iodine out
    # - texp=3 second
    set_itime(3)
    # - one exposure
    take_exposure(n=1)
    # - -> check saturation: < 20,000 counts on middle chip?
    # - -> Check I2 line depth. In center of chip, it should be ~30%
    print('IMPORTANT:')
    print('Check saturation: < 20,000 counts on middle chip?')
    print('Check I2 line depth. In center of chip, it should be ~30%')
    print()
    print('If you are not happy with the exposure, adjust the exposure time')
    print('in the HIRES dashboard and take a new exposure.  Continute until')
    print('you have an exposure which satisfies the above checks.')
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        print('Exiting calibrations script.')
        return False

    # Iodine Cell Calibrations B5
    # - Make sure cell is fully warmed up before taking these
    check_iodine_temps()
    # - Exposure meter off
    # - Quartz2 on
    set_lamp('quartz2')
    # - Lamp filter=ng3
    # - m deckname=B5
    set_decker('B5')
    # - iodine in
    iodine_in()
    # - texp=2 second
    set_itime(2)
    # - one exposure
    take_exposure(n=1)
    # - -> check saturation: < 20,000 counts on middle chip?
    # - -> Check I2 line depth. In center of chip, it should be ~30%
    print('IMPORTANT:')
    print('Check saturation: < 20,000 counts on middle chip?')
    print('Check I2 line depth. In center of chip, it should be ~30%')
    print()
    print('If you are not happy with the exposure, adjust the exposure time')
    print('in the HIRES dashboard and take a new exposure.  Continute until')
    print('you have an exposure which satisfies the above checks.')
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        print('Exiting calibrations script.')
        return False

    # Wide Flat Fields
    # - Exposure meter off
    # - Quartz2 on
    # - Lamp filter=ng3
    # - m deckname=C1
    set_decker('C1')
    # - iodine out
    iodine_out()
    # - texp=1 second
    set_itime(1)
    # - Take 1 exposures
    take_exposure(n=1)
    # - -> Check one test exp for saturation (<20k counts)
    print('IMPORTANT:')
    print('Check saturation: middle chip should have 10,000 < counts < 20,000')
    print()
    print('If you are not happy with the exposure, adjust the exposure time')
    print('in the HIRES dashboard and take a new exposure.  Continute until')
    print('you have an exposure which satisfies the above checks.')
    print()
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        new_exp_time = input('New Exposure Time (s)? ')
        try:
            new_exp_time = int(new_exp_time)
        except ValueError:
            print('New exposure time must be an integer.')
            new_exp_time = input('New Exposure Time (s)? ')
            new_exp_time = int(new_exp_time)
        set_itime(new_exp_time)
    # - Take 49 exposures
    print('Taking 49 additional flats.  This will take some time ...')
    take_exposure(n=49)
    # - m lampname=none
    set_lamp('none')
    # - m deckname=C2
    set_decker('C2')
    # - Check dewar level, if below threshold, fill
    if estimate_dewar_time() < 12:
        fill_dewar()



if __name__ == '__main__':
    pass
