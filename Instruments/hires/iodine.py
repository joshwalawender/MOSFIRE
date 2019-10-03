from .core import *


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
