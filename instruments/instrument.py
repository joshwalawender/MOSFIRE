import logging
from pathlib import Path


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_log(name='KeckInstrument', loglevel=logging.INFO, logfile=None):
    if type(loglevel) == str:
        loglevel = getattr(logging, loglevel.upper())
    log = logging.getLogger(name)

    if len(log.handlers) == 0:
        log.setLevel(logging.DEBUG)
        ## Set up console output
        LogConsoleHandler = logging.StreamHandler()
        LogConsoleHandler.setLevel(loglevel)
        LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
        LogConsoleHandler.setFormatter(LogFormat)
        log.addHandler(LogConsoleHandler)
        ## Set up file output
        if logfile is not None:
            logfile = Path(logfile).expanduser()
            if logfile.parent.exists() and logfile.parent.is_dir():
                LogFileHandler = logging.FileHandler(logfile)
                LogFileHandler.setLevel(logging.DEBUG)
                LogFileHandler.setFormatter(LogFormat)
                log.addHandler(LogFileHandler)
    
    return log
