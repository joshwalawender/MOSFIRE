from .core import *


##-------------------------------------------------------------------------
## HIRES Mechanisms
##-------------------------------------------------------------------------
def lights_are_on():
    """Returns True if lights are on in the enclosure.
    """
    log.info('Getting status of enclosure lights ...')
    lights_str = get('hires', 'lights')
    log.info(f'  lights are {lights_str}')
    return (lights_str == 'on')


def door_is_open():
    """Returns True if the door to the enclosure is open.
    """
    log.info('Getting status of enclosure door ...')
    door_str = get('hires', 'door')
    log.info(f'  door is {door_str}')
    return (door_str == 'open')


def collimator():
    """Determine which collimator is in the beam.  Returns a string of
    'red' or 'blue' indicating which is in beam.  Returns None if it can
    not interpret the result.
    """
    log.info('Getting current collimator ...')
    collred = get('hires', 'COLLRED')
    collblue = get('hires', 'COLLBLUE')
    if collred == 'red' and collblue == 'not blue':
        result = 'red'
    elif collred == 'not red' and collblue == 'blue':
        result = 'blue'
    else:
        result = None
    log.info(f'  collimator = {result}')
    return result


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
    collimator = collimator()
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


def xdang():
    return get('hires', 'XDANGL', mode=float)


def xdraw():
    return get('hires', 'XDRAW', mode=int)


def set_xdang(dest, simple=False, threshold=0.5, step=0.5):
    log.info(f'Moving XDANGL to {dest:.3f} deg')
    if simple is True:
        log.debug(f"Making simple move to {dest:.3f}")
        set('hires', 'XDANGL', dest, wait=True)
    else:
        delta = dest - xdang()
        log.debug(f'Total move is {delta:.3f} deg')
        if abs(delta) > threshold:
            nsteps = int(np.floor(abs(delta) / step))
            log.debug(f"Will move in {nsteps+1} steps")
            for i in range(nsteps):
                movedest = xdang() + np.sign(delta)*step
                log.debug(f"Making intermediate move to {movedest:.3f}")
                set('hires', 'XDANGL', movedest, wait=True)
                sleep(1)
        log.debug(f"Making final move to {dest:.3f}")
        set('hires', 'XDANGL', dest, wait=True)
    log.info(f"Done.  XDANGL = {xdang():.3f} deg")
    return XDANG


def set_xdraw(dest, simple=False, threshold=2000, step=2000):
    log.info(f'Moving XDRAW to {dest:.3f} counts')
    if simple is True:
        log.debug(f"Making simple move to {dest:.3f}")
        set('hires', 'XDRAW', dest, wait=True)
    else:
        delta = dest - xdraw()
        log.debug(f'Total move is {delta:.3f} counts')
        if abs(delta) > threshold:
            nsteps = int(np.floor(abs(delta) / step))
            log.debug(f"Will move in {nsteps+1} steps")
            for i in range(nsteps):
                movedest = xdraw() + np.sign(delta)*step
                log.debug(f"Making intermediate move to {movedest:.3f}")
                set('hires', 'XDRAW', movedest, wait=True)
                sleep(1)
        log.debug(f"Making final move to {dest:.3f}")
        set('hires', 'XDRAW', dest, wait=True)
    log.debug(f"Done.  XDRAW = {xdraw():.3f} steps")
    return XDRAW


def set_cafraw(cafraw, wait=True):
    log.info(f'Setting CAFRAW to {cafraw:.3f}')
    set('hires', 'cafraw', cafraw, wait=wait)


def set_cofraw(cofraw, wait=True):
    log.info(f'Setting COFRAW to {cofraw:.3f}')
    set('hires', 'cofraw', cofraw, wait=wait)


def set_tvfilter(tvf1name, wait=True):
    log.info(f'Setting TVF1NAME to {tvf1name}')
    set('hires', 'TVF1NAME', tvf1name, wait=wait)

