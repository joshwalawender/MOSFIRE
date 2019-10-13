from pathlib import Path

from .core import *
from .mechs import *

##-------------------------------------------------------------------------
## MOSFIRE Exposure Control Functions
##-------------------------------------------------------------------------
def exptime():
    '''Returns the exposure time per coadd in seconds.'''
    return get('ITIME', mode=int)/1000


def set_exptime(exptime):
    '''Set exposure time per coadd in seconds.  Note the ITIME keyword uses ms.
    '''
    log.info(f'Setting exposure time to {int(exptime*1000)} ms')
    set('ITIME', int(exptime*1000))


def coadds():
    '''Returns the number of coadds.'''
    return get('COADDS', mode=int)


def set_coadds(coadds):
    '''Set number of coadds
    '''
    log.info(f'Setting number of coadds to {int(coadds)}')
    set('COADDS', int(coadds))


def sampmode():
    '''Returns the sampling mode as an integer.'''
    return get('SAMPMODE', mode=int)


def parse_sampmode(input):
    if type(input) is int:
        sampmode = input
        numreads = None
    if type(input) is str:
        sampmode, numreads = sampmode_names.get(input)
    return (sampmode, numreads)


def set_sampmode(input):
    '''Set sampling mode.
    
    Input can be either an integer corresponding to the keyword value or it
    can be a string ('CDS', 'MCDS', 'MCDS16') which will be interpreted.
    
    If the 'MCDS16' string input is used, this will set *both* the sampling
    mode and the number of reads.
    '''
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
    '''Block and wait for the current exposure to be complete.
    '''
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
    '''Take an exposure.
    
    If the exptime, coadds, sampmode inputs are specified, those parameters for
    the exposure will be set prior to triggering the exposure.
    '''
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
    '''Alias take_exposure to goi
    '''
    goi(exptime=exptime, coadds=coadds, sampmode=sampmode, wait=wait)


def filename():
    '''Return the current filename value as a `pathlib.Path` object.
    '''
    return Path(get('FILENAME'))


def lastfile():
    '''Return the last filename value as a `pathlib.Path` object.
    
    This also checks that the file exists.  If it does not, it checks a
    similar path with /s prepended.  This handles the vm-mosfire machine case.
    '''
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
