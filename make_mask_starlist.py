#! @KPYTHON3@

## Import General Tools
import inspect
from pathlib import Path
import argparse
import logging
import re

from mosfire.mask import Mask

description = '''
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
log = logging.getLogger('MyLogger')
log.setLevel(logging.DEBUG)
## Set up console output
LogConsoleHandler = logging.StreamHandler()
if args.verbose:
    LogConsoleHandler.setLevel(logging.DEBUG)
else:
    LogConsoleHandler.setLevel(logging.INFO)
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
## The Instrument Script
##-------------------------------------------------------------------------
def make_mask_starlist(filename='~/mask_starlist.txt',
                       skipprecond=False, skippostcond=True):
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
    starlist_file = Path(filename).expanduser()
    if starlist_file.exists(): starlist_file.unlink()
    
    CSUmask_filepath = Path('~/CSUmasks').expanduser()
    log.info(f'Looking for masks in {CSUmask_filepath}')

    with open(starlist_file, 'w') as starlist:
        for file in CSUmask_filepath.glob('**/*.xml'):
            mask = Mask(file)
            if re.match('long2pos', mask.name):
                log.warning(f'Skipping {mask.name} from {file}')
            elif re.match('LONGSLIT\-\d+x\d+', mask.name):
                log.warning(f'Skipping {mask.name} from {file}')
            else:
                log.info(f'Processing mask file: {file}')
                equinox = mask.equinox if hasattr(mask, 'equinox') else 2000
                if len(mask.name) <= 16:
                    mask_name = mask.name
                    comment = ''
                else:
                    mask_name = mask.name[:16]
                    comment = f'# full mask name = {mask.name}'
                line = (f'{mask_name:16s} '
                        f'{mask.center.to_string("hmsdms", sep=" ", precision=2)} '
                        f'{equinox:7.2f} '
                        f'rotdest={mask.PA:+.2f} rotmode=PA {comment}')
                starlist.write(f'{line}\n')

    ##-------------------------------------------------------------------------
    ## Post-Condition Checks
    if skippostcond is True:
        log.debug('Skipping post condition checks')
    else:
        pass


if __name__ == '__main__':
    make_mask_starlist()
