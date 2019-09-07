import logging

##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
def create_log(name='KeckInstrument', loglevel=logging.INFO):
    if type(loglevel) == str:
        loglevel = getattr(logging, loglevel.upper())
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    LogConsoleHandler.setLevel(loglevel)
    LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
    ## Set up file output
    # LogFileName = None
    # LogFileHandler = logging.FileHandler(LogFileName)
    # LogFileHandler.setLevel(logging.DEBUG)
    # LogFileHandler.setFormatter(LogFormat)
    # log.addHandler(LogFileHandler)
    
    return log


##-------------------------------------------------------------------------
## Import KTL python
##-------------------------------------------------------------------------
# Wrap ktl import in try/except so that we can maintain test case or
# simulator version of functions on machines without KTL installed.

def connect_to_ktl(instrumentName, serviceNames, noactions=False):
    log = logging.getLogger(instrumentName)
    if noactions is True:
        ktl = None
    else:
        try:
            import ktl
            from ktl import Exceptions as ktlExceptions
        except ModuleNotFoundError:
            ktl = None
        except ktlExceptions.ktlError:
            ktl = None

    # Connect to KTL Services
    services = {}
    if ktl is not None:
        for service in serviceNames:
            try:
                services[service] = ktl.Service(service)
            except ktlExceptions.ktlError as e:
                log.error(f"ERROR: Failed to connect to service {service}")
                log.error(e)

        log.info(f'Connected {len(services)} / {len(serviceNames)} services')
    return services
