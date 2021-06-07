#! /usr/bin/env kpython3

## Import General Tools
import inspect
from datetime import datetime
from datetime import timedelta
from time import sleep
from pathlib import Path
import argparse
import logging
import re

description = '''Parse mds logs and find aborted exposures and read timeouts.
'''

##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description=description)
## add flags
p.add_argument("-v", "--verbose", dest="verbose",
    default=False, action="store_true",
    help="Be verbose! (default = False)")
args = p.parse_args()


##-------------------------------------------------------------------------
## Create logger object
##-------------------------------------------------------------------------
log = logging.getLogger('FindReadTimeouts')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
if args.verbose:
    LogConsoleHandler.setLevel(logging.DEBUG)
else:
    LogConsoleHandler.setLevel(logging.WARNING)
LogFormat = logging.Formatter('%(asctime)s %(levelname)8s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
LogConsoleHandler.setFormatter(LogFormat)
log.addHandler(LogConsoleHandler)
## Set up file output
# LogFileName = None
# LogFileHandler = logging.FileHandler(LogFileName)
# LogFileHandler.setLevel(logging.DEBUG)
# LogFileHandler.setFormatter(LogFormat)
# log.addHandler(LogFileHandler)


##-------------------------------------------------------------------------
## find_read_timeouts
##-------------------------------------------------------------------------
def find_read_timeouts(logfile='/s/sdata1300/syslogs/MDS.log',
                       skipprecond=False, skippostcond=True):
    this_script_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_script_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        if not isinstance(logfile, Path):
            logfile = Path(logfile)
        if logfile.exists() is not True:
            raise FileNotFoundError(f'Could not find logfile {logfile}')
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    aborted_files = {'Read Timeout': [], 'Abort': []}
    all_files = []
    log.info(f'Reading: {logfile}')
    with open(logfile, 'r') as fileobj:
        while True:
            lines = fileobj.readlines(100000)
            if not lines:
                break
            for i,line in enumerate(lines):
                match_filename = re.search('lastFilename = (Z:.+\\\\)([\w\d_]+\.fits)', line)
                if match_filename is not None:
                    filename = match_filename.group(2)
                    all_files.append(filename)

                find_abort = re.search('Exposure Aborted.*: Fits writing complete', line)
                if find_abort is not None:
                    find_timeout = re.search('Exposure Aborted \(Read Timeout\): Fits writing complete', line)
                    type_str = {True: 'Read Timeout', False: 'Abort'}[(find_timeout is not None)]
                    match_filename = re.search('lastFilename = (Z:.+\\\\)([\w\d_]+\.fits)', lines[i+1])
                    if match_filename is not None:
                        filename = match_filename.group(2)
                        log.info(f'  Found {type_str} on file {filename}')
                    else:
                        filename = ''
                        print(lines[i:i+5])
                        log.warning(f'  Found {type_str} with no file')
                    aborted_files[type_str].append(filename)

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass

    return all_files, aborted_files


##-------------------------------------------------------------------------
## find_read_timeouts_by_year
##-------------------------------------------------------------------------
def find_read_timeouts_by_year(year, skipprecond=False, skippostcond=True):
    this_script_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_script_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        if isinstance(year, int) is False:
            raise FailedCondition(f'Input: {year} must be 2 digit int')
    
    ##-------------------------------------------------------------------------
    ## Script Contents
    
    abort_file = Path(f'/s/sdata1300/logs/server/mds/aborts_20{year}.log')
    if abort_file.exists() is True:
        with open(abort_file, 'r') as abort_file_obj:
            lines = abort_file_obj.readlines()
            pattern = 'Count of Read Timeout/Aborted/Total = (\d+)/(\d+)/(\d+)'
            first_line_match = re.match(pattern, lines[0])
            if first_line_match is not None:
                nall0 = int(first_line_match.group(3))
                naborted0 = int(first_line_match.group(2))
                ntimeout0 = int(first_line_match.group(1))
            else:
                log.warning('First line not matched:')
                log.warning(lines[0])
                nall0 = 0
                naborted0 = 0
                ntimeout0 = 0
        abort_file.unlink()
    else:
        nall0 = 0
        naborted0 = 0
        ntimeout0 = 0
    aborted_files = {'Read Timeout': [], 'Abort': []}
    all_files = []

    logfiles = [lf for lf in Path('/s/sdata1300/logs/server/mds/').glob(f'{year}*_mds.log')]
    logfiles.sort()

    log.info(f'## Building abort count for {len(logfiles)} log files in 20{year} ##')

    for logfile in logfiles:
        new_all_files, new_aborted_files = find_read_timeouts(logfile=logfile)
        all_files.extend(new_all_files)
        aborted_files['Read Timeout'].extend(new_aborted_files['Read Timeout'])
        aborted_files['Abort'].extend(new_aborted_files['Abort'])

    nall = len(all_files)
    naborted = len(aborted_files['Abort'])
    ntimeout = len(aborted_files['Read Timeout'])
    with open(abort_file, 'w') as abortfileobj:
        abortfileobj.write(f'Count of Read Timeout/Aborted/Total = {ntimeout}/{naborted}/{nall}\n')
        abortfileobj.write(f'Percent of Read Timeout/Aborted = {ntimeout/nall:.2%}/{naborted/nall:.2%}\n')

        abortfileobj.write(f'\nRead Timeout:\n')
        for filename in aborted_files['Read Timeout']:
            abortfileobj.write(f'{filename}\n')
        abortfileobj.write(f'\nAborted:\n')
        for filename in aborted_files['Abort']:
            abortfileobj.write(f'{filename}\n')

    new_all = nall - nall0
    new_aborted = naborted - naborted0
    new_timeout = ntimeout - ntimeout0

    if new_aborted > 0 or new_timeout > 0:
        print(f'{new_timeout} new Read Timeouts')
        print(f'{new_aborted} new Aborts')
        print(f'out of {new_all} new frames taken')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass


##-------------------------------------------------------------------------
## generate_read_timeout_history
##-------------------------------------------------------------------------
def generate_read_timeout_history(skipprecond=False, skippostcond=True):
    '''Loop through years since 2012, process all mds log files, and write
    aborted files.
    '''
    this_script_name = inspect.currentframe().f_code.co_name
    log.debug(f"Executing: {this_script_name}")

    ##-------------------------------------------------------------------------
    ## Pre-Condition Checks
    if skipprecond is True:
        log.debug('Skipping pre condition checks')
    else:
        pass
    
    ##-------------------------------------------------------------------------
    ## Script Contents

    now_year = int(datetime.now().strftime('%y'))
    year = 12

    while year <= now_year:
        find_read_timeouts_by_year(year)
        year += 1

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass


if __name__ == '__main__':
    now_year = int(datetime.now().strftime('%y'))
    find_read_timeouts_by_year(now_year)
