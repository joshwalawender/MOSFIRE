from pathlib import Path

from .core import *
from .mechs import *

##-------------------------------------------------------------------------
## MOSFIRE Exposure Control Functions
##-------------------------------------------------------------------------
def exptime():
    return get('EXPTIME', mode=int)/1000


def set_exptime(exptime):
    '''Set exposure time per coadd in seconds.  Note the ITIME keyword uses ms.
    '''
    log.info(f'Setting exposure time to {int(exptime*1000)} ms')
    set('ITIME', int(exptime*1000))


def coadds():
    return get('COADDS', mode=int)


def set_coadds(coadds):
    '''Set number of coadds
    '''
    log.info(f'Setting number of coadds to {int(coadds)}')
    set('COADDS', int(coadds))


def sampmode():
    return get('SAMPMODE', mode=int)


def parse_sampmode(input):
    if type(input) is int:
        sampmode = input
        numreads = None
    if type(input) is str:
        sampmode, numreads = sampmode_names.get(input)
    return (sampmode, numreads)


def set_sampmode(input):
    log.info(f'Setting Sampling Mode to {input}')
    sampmode, numreads = parse_sampmode(input)
    if sampmode in allowed_sampmodes:
        log.debug(f'Setting Sampling Mode to: {sampmode}')
        set('sampmode', sampmode)
        if numreads is not None:
            log.debug(f'Setting Number of Reads: {numreads}')
            set('numreads', numreads)
    else:
        log.error(f'Sampling mode {sampmode} is not supported')


def waitfor_exposure(timeout=300, noshim=False):
    log.debug('Waiting for exposure to finish')
    if noshim is False:
        sleep(1)
    done = get('imagedone', mode=bool) and get('ready', service='mds', mode=bool)
    endat = dt.utcnow() + tdelta(seconds=timeout)
    while done is False and dt.utcnow() < endat:
        sleep(1)
        done = get('imagedone', mode=bool) and get('ready', service='mds', mode=bool)
    if done is False:
        log.warning(f'Timeout exceeded on waitfor_exposure to finish')
    return done


def wfgo(timeout=300, noshim=False):
    '''Alias waitfor_exposure to wfgo
    '''
    waitfor_exposure(timeout=timeout, noshim=noshim)


def goi(exptime=None, coadds=None, sampmode=None, wait=True):
    waitfor_exposure(noshim=True)
    if exptime is not None:
        set_exptime(exptime)
    if coadds is not None:
        set_coadds(coadds)
    if sampmode is not None:
        set_sampmode(sampmode)
    log.info('Taking exposure')
    set('go', '1')
    if wait is True:
        waitfor_exposure()
        imagefile = Path(lastfile())
        if imagefile.exists():
            log.info(f'  Found last file {imagefile.name}')
        else:
            log.warning(f'Did not find file: {imagefile}')


def take_exposure(exptime=None, coadds=None, sampmode=None, wait=True):
    goi(exptime=exptime, coadds=coadds, sampmode=sampmode, wait=wait)


def filename():
    return Path(get('FILENAME'))


def lastfile():
    lastfile = Path(get('LASTFILE'))
    if lastfile.exists():
        return lastfile
    else:
        # Check and see if we need a /s prepended on the path for this machine
        trypath = Path('/s')
        for part in lastfile.parts[1:]:
            trypath = trypath.joinpath(part)
        if not trypath.exists():
            log.warning(f'Could not find last file on disk: {lastfile}')
        else:
            return trypath


def waitfor_FCS(timeout=60, PAthreshold=0.1, ELthreshold=0.1, noshim=False):
    '''Wait for FCS to get close to actual PA and EL.
    '''
    log.debug('Waiting for FCS to reach destination')
    if noshim is False:
        sleep(1)
    telPA = get('PA', service='mfcs', mode=float)
    telEL = get('EL', service='mfcs', mode=float)
    fcsPA, fcsEL = get('PA_EL', service='mfcs', mode=str).split()
    fcsPA = float(fcsPA)
    fcsEL = float(fcsEL)
    PAdiff = abs(fcsPA - telPA)
    ELdiff = abs(fcsEL - telEL)
    done = (PAdiff < PAthreshold) and (ELdiff < ELthreshold)
    endat = dt.utcnow() + tdelta(seconds=timeout)
    while done is False and dt.utcnow() < endat:
        sleep(1)
        done = (PAdiff < PAthreshold) and (ELdiff < ELthreshold)
    if done is False:
        log.warning(f'Timeout exceeded on waitfor_FCS to finish')
    return done
