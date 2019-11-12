from .core import *

import re
from time import sleep

try:
    import ktl
except:
    ktl = None

def binning():
    """Return the binning value, a tuple of (binX, binY).
    """
    binningkwstr = get('hiccd', 'BINNING')
    binningmatch = re.match('\\n\\tXbinning (\d)\\n\\tYbinning (\d)',
                            binningkwstr)
    if binningmatch is not None:
        binningval = (int(binningmatch.group(1)), int(binningmatch.group(2)))
        log.debug(f'binning = {binningval}')
        return binningval
    else:
        log.error(f'Could not parse keyword value "{binningkwstr}"')
        return None


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


def windowing():
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


def gain():
    """Return the gain as a string 'low' or 'high'.
    """
    return get('hiccd', 'CCDGAIN')


def set_gain(input):
    """Set the gain as a string 'low' or 'high'.
    """
    if input.lower() not in ['high', 'low']:
        log.error(f"Gain {input} not understood.  Gain not set.")
        return None
    set('hiccd', 'CCDGAIN', input.lower())


def ccdspeed():
    """Return the CCD readout speed as a string.
    """
    return get('hiccd', 'CCDSPEED')


def exptime():
    get('hiccd', 'TTIME', mode=int)


def set_exptime(exptime):
    set('hiccd', 'TTIME', exptime)


def is_writing():
    return get('hiccd', 'WCRATE', mode=bool)


def obstype():
    result = get('hiccd', 'obstype')
    assert result in obstypes
    return result


def set_obstype(myobstype):
    log.info(f'Setting OBSTYPE to "{myobstype}"')
    if myobstype in obstypes:
        set('hiccd', 'obstype', myobstype)
        return obstype()
    else:
        log.error(f'OBSTYPE {myobstype} not recognized.')
        log.error(f'Allowed obstypes:')
        for otype in obstypes:
            log.error(f'  {otype}')


def wait_for_observip(timeout=300):
    if get('hiccd', 'OBSERVIP', mode=bool) is True:
        log.info(f'Waiting up to {timeout} seconds for observation to finish')
        if not ktl.waitFor('($hiccd.OBSERVIP == False )', timeout=timeout):
            raise Exception('Timed out waiting for OBSERVIP')


def goi(type=None, exptime=None, nexp=1, timeshim=True):
    """Takes one or more exposures of the given exposure time and type.
    Modeled after goi script.
    """
    if type is None:
        type = obstype()
    if type not in obstypes:
        log.warning(f'OBSTYPE "{type} not understood"')
        return None

    wait_for_observip()

    if exptime is not None:
        set_exptime(int(exptime))

    if type.lower() in ["dark", "bias", "zero"]:
        set('hiccd', 'AUTOSHUT', False)
    else:
        set('hiccd', 'AUTOSHUT', True)

    for i in range(nexp):
        exptime = get('hiccd', 'TTIME', mode=int)
        log.info(f"Taking exposure {i+1:d} of {nexp:d}")
        log.info(f"  Exposure Time = {exptime:d} s")
        set('hiccd', 'EXPOSE', True)
        if timeshim is True: sleep(1)
        exposing = ktl.Expression("($hiccd.OBSERVIP == True) "
                                  "and ($hiccd.EXPOSIP == True )")
        reading = ktl.Expression("($hiccd.OBSERVIP == True) "
                                 "and ($hiccd.WCRATE == True )")
        obsdone = ktl.Expression("($hiccd.OBSERVIP == False)")

        if not exposing.wait(timeout=30) and exptime > 2:
            raise Exception('Timed out waiting for EXPOSING to start')
        log.info('  Exposing ...')

        if not reading.wait(timeout=exptime+30):
            raise Exception('Timed out waiting for READING to start')
        log.info('  Reading out ...')

        if not obsdone.wait(timeout=90):
            raise Exception('Timed out waiting for READING to finish')
        sleep(0.5)
        lf = lastfile()
        if lf.exists():
            log.info(f"  Found image file: {lf}")
        else:
            log.warning(f"  Image file {lf} not found on disk")
        log.info('Done')


def take_exposure(type=None, exptime=None, nexp=1, timeshim=True):
    '''Alias take_exposure to goi
    '''
    goi(type=type, exptime=exptime, nexp=nexp, timeshim=timeshim)


def lastfile():
    OUTDIR = get('hiccd', 'OUTDIR')
    OUTFILE = get('hiccd', 'OUTFILE')
    LFRAMENO = get('hiccd', 'LFRAMENO', mode=int)
    last_file = Path(OUTDIR).joinpath(f"{OUTFILE}{LFRAMENO:04d}.fits")
    return last_file
