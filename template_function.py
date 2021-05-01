import inspect

try:
    import ktl
except ModuleNotFoundError as e:
    pass


##-----------------------------------------------------------------------------
## Instrument Function
##-----------------------------------------------------------------------------
def function(arguments, skipprecond=False, skippostcond=False):
    '''docstring
    '''
    this_function_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_function_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        if condition1 is not True:
            raise FailedCondition('description of failure')
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    # ----> insert instrument script here <----
    
    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        if condition2 is not True:
            raise FailedCondition('description of failure')

    return None


def function_with_args():
    description = '''
    '''
    p = argparse.ArgumentParser(description=description)
    ## add flags
    p.add_argument("-v", "--verbose", dest="verbose",
        default=False, action="store_true",
        help="Be verbose! (default = False)")
    ## add options
    p.add_argument("--input", dest="input", type=str,
        help="The input.")
    ## add arguments
    p.add_argument('argument', type=int,
                   help="A single argument")
    p.add_argument('allothers', nargs='*',
                   help="All other arguments")
    args = p.parse_args()
    function(**args)
