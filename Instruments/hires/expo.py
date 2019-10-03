from .core import *


def get_expo_status():
    return get('expo', 'EXM0STA')


def expo_on():
    log.info('Turning exposure meter on')
    set('expo', 'EXM0MOD', 'On')


def expo_off():
    log.info('Turning exposure meter off')
    set('expo', 'EXM0MOD', 'Off')
