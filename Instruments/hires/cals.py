from .core import *


def get_lamp():
    return get('hires', 'LAMPNAME')


def set_lamp(lampname, wait=True):
    if lampname not in lampnames:
        log.error(f"{lampname} not known")
        log.error(f"Available lamps: {lampnames}")
    log.info(f'Setting lamp to {lampname}')
    set('hires', 'LAMPNAME', lampname, wait=wait)
    if wait is True:
        assert get_lamp() == lampname


def get_lamp_filter():
    return get('hires', 'LFILNAME')


def set_lamp_filter(lfilname, wait=True):
    assert lfilname in ['bg12', 'bg13', 'bg14', 'bg38', 'clear', 'dt',
                        'etalon', 'gg495', 'ng3', 'ug1', 'ug5']
    set('hires', 'LFILNAME', lfilname, wait=wait)
    assert get_lamp_filter() == lfilname
