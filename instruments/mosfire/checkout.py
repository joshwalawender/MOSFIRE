#!kpython3

import numpy as np

from .core import *
from .mask import Mask
from .filter import is_dark, go_dark
from .obsmode import set_obsmode
from .metadata import lastfile
from .detector import take_exposure
from .csu import setup_mask, execute_mask, initialize_bars, physical_to_pixel
from .rotator import safe_angle
from .domelamps import dome_flat_lamps
from .analysis import verify_mask_with_image


##-------------------------------------------------------------------------
## MOSFIRE Checkout
##-------------------------------------------------------------------------
def checkout(quick=False, tolerance=3.2):
    '''Perform a basic checkout of the MOSFIRE instrument.  The normal
    execution of this script performs a standard pre-run checkout.  The quick
    version performs a shorter, less complete checkout to be used when there is
    limited time.
    '''
    # Check if MOSFIRE is the selected instrument and if we are at a safe angle
    INSTRUMEkw = ktl.cache(service='dcs', keyword='INSTRUME')
    if INSTRUMEkw.read() == 'MOSFIRE':
        safe_angle()
    else:
        log.warning("MOSFIRE is not the selected instrument.")
        log.warning("Will ask user to verify safe angle before proceeding.")
        print("  --------------------------------------------------------")
        print("  This checkout script moves CSU bars, please confirm that")
        print("  the instrument is at a safe rotator angle.")
        print("  --------------------------------------------------------")
        print()
        result = input('Is MOSFIRE at a safe angle? [y/n] ')
        if result.lower() not in ['y', 'yes']:
            log.critical('Exiting script.')
            return False

    log.info(f'Executing checkout script.')

    log.info('Checking that instrument is dark')
    go_dark()

    log.info('Checking mechanisms')
    mechanisms_ok()

    log.info('Taking dark image')
    take_exposure(exptime=2, coadds=1, sampmode='CDS', object='Test Dark')

    log.info(f'Please verify that {lastfile()} looks normal for a dark image')
    proceed = input('Continue? [y] ')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        log.critical('Exiting script.')
        return False

    # Quick checkout
    if quick is True:
        log.info('Setup 46x2.7 long slit mask')
        wideslit = Mask('46x2.7')
        setup_mask(wideslit)
        log.info('Execute mask')
        execute_mask(override=True)
        log.info('Taking 2.7" wide long slit image')
        set_obsmode('K-imaging')
        take_exposure(exptime=6, coadds=1, sampmode='CDS', object='2.7" Long Slit')
        wideSlitFile = lastfile()
        log.info('Going dark')
        go_dark()
        verify_mask_with_image(wideslit, wideSlitFile, tolerance=tolerance)

        log.info('Setup 46x0.7 long slit mask')
        longslit = Mask('46x0.7')
        setup_mask(longslit)
        log.info('Execute mask')
        execute_mask(override=True)
        log.info('Taking long slit image')
        set_obsmode('K-imaging')
        take_exposure(exptime=6, coadds=1, sampmode='CDS', object='0.7" Long Slit')
        narrowSlitFile = lastfile()
        log.info('Going dark')
        go_dark()
        verify_mask_with_image(longslit, narrowSlitFile, tolerance=tolerance)

    # Normal (long) checkout
    if quick is False:
        log.info('Setup OPEN mask')
        setup_mask(Mask('OPEN'))
        execute_mask(override=True)
        log.info('Initializing all bars')
        initialize_bars('all')

        log.info('Taking open mask image')
        set_obsmode('K-imaging', wait=True)
        take_exposure(exptime=6, coadds=1, sampmode='CDS')
        openMaskFile = lastfile()
        go_dark()

        log.info('Setup 0.7x46 long slit mask')
        setup_mask(Mask('0.7x46'))
        log.info('Execute mask')
        execute_mask(override=True)
        log.info('Taking long slit image')
        set_obsmode('K-imaging')
        take_exposure(exptime=6, coadds=1, sampmode='CDS')
        narrowSlitFile = lastfile()
        go_dark()


## ------------------------------------------------------------------
## Expected bar positions
## ------------------------------------------------------------------
expect_longslit = {1: 981.9, 2: 975.7, 3: 984.7, 4: 978.6, 5: 987.5, 6: 981.3,
                   7: 990.7, 8: 984.2, 9: 993.4, 10: 987.2, 11: 996.1,
                   12: 989.9, 13: 999.3, 14: 992.8, 15: 1002.1, 16: 995.9,
                   17: 1004.8, 18: 998.7, 19: 1007.7, 20: 1001.5, 21: 1010.3,
                   22: 1004.8, 23: 1013.1, 24: 1007.8, 25: 1014.0, 26: 1012.5,
                   27: 1018.9, 28: 1013.1, 29: 1021.6, 30: 1016.4, 31: 1024.6,
                   32: 1019.0, 33: 1027.1, 34: 1022.2, 35: 1029.3, 36: 1026.1,
                   37: 1033.4, 38: 1027.8, 39: 1035.2, 40: 1032.1, 41: 1039.0,
                   42: 1033.7, 43: 1042.0, 44: 1036.3, 45: 1044.8, 46: 1039.1,
                   47: 1047.4, 48: 1042.0, 49: 1050.5, 50: 1044.8, 51: 1053.2,
                   52: 1047.7, 53: 1056.3, 54: 1050.4, 55: 1059.1, 56: 1053.3,
                   57: 1062.2, 58: 1056.2, 59: 1064.9, 60: 1059.0, 61: 1067.9,
                   62: 1061.9, 63: 1070.8, 64: 1064.8, 65: 1073.5, 66: 1067.7,
                   67: 1076.4, 68: 1070.6, 69: 1079.4, 70: 1073.5, 71: 1082.2,
                   72: 1076.4, 73: 1085.1, 74: 1079.1, 75: 1088.0, 76: 1082.1,
                   77: 1090.8, 78: 1084.8, 79: 1093.6, 80: 1087.8, 81: 1096.5,
                   82: 1090.6, 83: 1099.3, 84: 1093.5, 85: 1102.3, 86: 1096.4,
                   87: 1105.1, 88: 1099.3, 89: 1108.1, 90: 1102.2,
                   91: 1110.9, 92: 1105.1}

expect_wideslit = {1: 987.7, 2: 970.0, 3: 990.5, 4: 972.8, 5: 993.4, 6: 975.4,
                   7: 996.9, 8: 978.0, 9: 999.6, 10: 981.0, 11: 1002.4,
                   12: 983.7, 13: 1005.4, 14: 986.6, 15: 1007.9, 16: 989.9,
                   17: 1010.9, 18: 992.7, 19: 1013.7, 20: 995.6, 21: 1016.7,
                   22: 998.4, 23: 1019.5, 24: 1001.3, 25: 1022.7, 26: 1003.9,
                   27: 1025.3, 28: 1006.8, 29: 1028.4, 30: 1009.8, 31: 1031.1,
                   32: 1012.7, 33: 1034.0, 34: 1015.4, 35: 1037.2, 36: 1018.4,
                   37: 1040.0, 38: 1021.3, 39: 1042.9, 40: 1023.9, 41: 1045.6,
                   42: 1027.0, 43: 1048.2, 44: 1030.0, 45: 1051.0, 46: 1032.9,
                   47: 1053.8, 48: 1035.7, 49: 1056.8, 50: 1038.7, 51: 1059.4,
                   52: 1041.7, 53: 1062.3, 54: 1044.4, 55: 1065.2, 56: 1047.3,
                   57: 1068.2, 58: 1050.1, 59: 1070.9, 60: 1053.1, 61: 1073.8,
                   62: 1056.0, 63: 1076.8, 64: 1058.9, 65: 1079.4, 66: 1061.8,
                   67: 1082.3, 68: 1064.8, 69: 1085.1, 70: 1067.6, 71: 1087.9,
                   72: 1070.7, 73: 1090.8, 74: 1073.4, 75: 1093.7, 76: 1076.3,
                   77: 1096.6, 78: 1079.2, 79: 1099.4, 80: 1082.1, 81: 1102.3,
                   82: 1084.8, 83: 1105.0, 84: 1087.8, 85: 1108.1, 86: 1090.7,
                   87: 1110.9, 88: 1093.6, 89: 1113.7, 90: 1096.5, 91: 1116.6,
                   92: 1099.4}

if __name__ == '__main__':
    import argparse
    ## Parse Command Line Arguments
    p = argparse.ArgumentParser(description=description)
    p.add_argument("-q", "--quick", dest="quick",
        default=False, action="store_true",
        help="Do a quick checkout instead of a full checkout.")
    args = p.parse_args()

    checkout(quick=args.quick)
