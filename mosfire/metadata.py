from .core import *


##-----------------------------------------------------------------------------
## OUTDIR
##-----------------------------------------------------------------------------
def outdir(skipprecond=False, skippostcond=False):
    '''Return outdir as a pathlib.Path object
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    OUTDIRkw = ktl.cache(service='mds', keyword='OUTDIR')
    OUTDIRp = Path(OUTDIRkw.read())

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return OUTDIRp


##-----------------------------------------------------------------------------
## set OUTDIR
##-----------------------------------------------------------------------------
def set_outdir(input, skipprecond=False, skippostcond=False):
    '''Set outdir
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        p = Path(input)
        if not p.parent.exists():
            trypath = Path('/s')
            for part in p.parent.parts[1:]:
                trypath = trypath.joinpath(part)
            if not trypath.exists():
                raise FailedCondition(f'Can not find parent directory for {input}')

    ##-------------------------------------------------------------------------
    ## Script Contents
    OUTDIRkw = ktl.cache(service='mds', keyword='OUTDIR')
    OUTDIRkw.write(input)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if OUTDIRkw.read() != input:
            raise FailedCondition(f'Failed to set outdir to "{input}"')
    
    return None


##-----------------------------------------------------------------------------
## object
##-----------------------------------------------------------------------------
def object(skipprecond=False, skippostcond=False):
    '''Return object as a string
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    objectkw = ktl.cache(service='mds', keyword='OBJECT')
    object_str = objectkw.read()

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return object_str


##-----------------------------------------------------------------------------
## set object
##-----------------------------------------------------------------------------
def set_object(input, skipprecond=False, skippostcond=False):
    '''Set the object keyword header value
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    objectkw = ktl.cache(service='mds', keyword='OBJECT')
    objectkw.write(input)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if objectkw.read() != input:
            raise FailedCondition(f'Failed to set object to "{input}"')
    
    return None


##-----------------------------------------------------------------------------
## observer
##-----------------------------------------------------------------------------
def observer(skipprecond=False, skippostcond=False):
    '''Return observer as a string
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    observerkw = ktl.cache(service='mosfire', keyword='OBSERVER')
    observer_str = observerkw.read()

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass
    
    return observer_str


##-----------------------------------------------------------------------------
## set observer
##-----------------------------------------------------------------------------
def set_observer(input, skipprecond=False, skippostcond=False):
    '''Set the object keyword header value
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")
    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    observerkw = ktl.cache(service='mosfire', keyword='OBSERVER')
    observerkw.write(input)
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if observerkw.read() != input:
            raise FailedCondition(f'Failed to set observer to "{input}"')
    
    return None


##-----------------------------------------------------------------------------
## filename
##-----------------------------------------------------------------------------
def filename(skipprecond=False, skippostcond=False):
    '''Return the current filename value as a `pathlib.Path` object.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    filenamekw = ktl.cache(service='mds', keyword='FILENAME')
    filename_path = Path(filenamekw.read())
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return filename_path


##-----------------------------------------------------------------------------
## lastfile
##-----------------------------------------------------------------------------
def lastfile(skipprecond=False, skippostcond=False):
    '''Return the last filename value as a `pathlib.Path` object.
    
    This also checks that the file exists.  If it does not, it checks a
    similar path with /s prepended.  This handles the vm-mosfire machine case.
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    lastfilekw = ktl.cache(service='mds', keyword='LASTFILE')
    lastfile_path = Path(lastfilekw.read())
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if lastfile_path.exists():
            log.debug(f'Found file at {lastfile_path}')
        else:
            trypath = Path('/s')
            for part in lastfile_path.parts[1:]:
                trypath = trypath.joinpath(part)
            if trypath.exists():
                log.debug(f'Found file at {trypath}')
                return trypath
            else:
                raise FailedCondition(f'Could not find last file on disk: {lastfile_path}')

    return lastfile_path
