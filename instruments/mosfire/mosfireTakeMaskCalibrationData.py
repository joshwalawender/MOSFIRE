#!kpython3

## Import General Tools
import argparse

from instruments.mosfire.core import log


description = '''
Example call:
python mosfireTakeMaskCalibrationData.py 0 2 0 2 1 mos 14 0 0 2 0 2 1 mos 14 0 0 2 0 2 1 mos 10 0 0 2 0 2 1 mos 10 0 0 2 0 2 1 mos 10 0 0 /home/mosfire8/CSUmasks/BT_masks/CC_hiz_agn_9/CC_hiz_agn_9.xml 1 1 1 1

0 2 0 2 1 mos 14 0
0 2 0 2 1 mos 10 0
0 2 0 2 1 mos 10 0
0 2 0 2 1 mos 10 0
0 2 0 2 1 mos 10 0
0 /home/mosfire8/CSUmasks/BT_masks/CC_hiz_agn_9/CC_hiz_agn_9.xml 1 1 1 1
'''

##-------------------------------------------------------------------------
## Parse Command Line Arguments
##-------------------------------------------------------------------------
## create a parser object for understanding command-line arguments
p = argparse.ArgumentParser(description=description)
## add arguments
p.add_argument('YNeonCount', type=int, help='number of Ne exposures to acquire in Y band')
p.add_argument('YNeonTime', type=int, help='exposures Time for Ne arcs in Y band')
p.add_argument('YArgonCount', type=int, help='number of Ar exposures to acquire in Y band')
p.add_argument('YArgonTime', type=int, help='exposures Time for Ar arcs in Y band')
p.add_argument('YFlatCount', type=int, help='number of Flats to acquire in Y band')
p.add_argument('YFlatLamp', type=str, help='lamp to use for Y-band flats')
p.add_argument('YFlatTime', type=int, help='exposure Time for Flats in Y band')
p.add_argument('YLampsOff', type=int, help='flag indicating whether to acquire Lamps on/Lamps Off pair in Y band')
p.add_argument('JNeonCount', type=int, help='number of Ne exposures to acquire in J band')
p.add_argument('JNeonTime', type=int, help='exposures Time for Ne arcs in J band')
p.add_argument('JArgonCount', type=int, help='number of Ar exposures to acquire in J band')
p.add_argument('JArgonTime', type=int, help='exposures Time for Ar arcs in J band')
p.add_argument('JFlatCount', type=int, help='number of Flats to acquire in J band')
p.add_argument('JFlatLamp', type=str, help='lamp to use for J-band flats')
p.add_argument('JFlatTime', type=int, help='exposure Time for Flats in J band')
p.add_argument('JLampsOff', type=int, help='flag indicating whether to acquire Lamps on/Lamps Off pair in J band')
p.add_argument('HNeonCount', type=int, help='number of Ne exposures to acquire in H band')
p.add_argument('HNeonTime', type=int, help='exposures Time for Ne arcs in H band')
p.add_argument('HArgonCount', type=int, help='number of Ar exposures to acquire in H band')
p.add_argument('HArgonTime', type=int, help='exposures Time for Ar arcs in H band')
p.add_argument('HFlatCount', type=int, help='number of Flats to acquire in H band')
p.add_argument('HFlatLamp', type=str, help='lamp to use for H-band flats')
p.add_argument('HFlatTime', type=int, help='exposure Time for Flats in H band')
p.add_argument('HLampsOff', type=int, help='flag indicating whether to acquire Lamps on/Lamps Off pair in H band')
p.add_argument('J2NeonCount', type=int, help='number of Ne exposures to acquire in J2 band')
p.add_argument('J2NeonTime', type=int, help='exposures Time for Ne arcs in J2 band')
p.add_argument('J2ArgonCount', type=int, help='number of Ar exposures to acquire in J2 band')
p.add_argument('J2ArgonTime', type=int, help='exposures Time for Ar arcs in J2 band')
p.add_argument('J2FlatCount', type=int, help='number of Flats to acquire in J2 band')
p.add_argument('J2FlatLamp', type=str, help='lamp to use for J2-band flats')
p.add_argument('J2FlatTime', type=int, help='exposure Time for Flats in J2 band')
p.add_argument('J2LampsOff', type=int, help='flag indicating whether to acquire Lamps on/Lamps Off pair in J band')
p.add_argument('KNeonCount', type=int, help='number of Ne exposures to acquire in K band')
p.add_argument('KNeonTime', type=int, help='exposure Time for Ne arcs in K band')
p.add_argument('KArgonCount', type=int, help='number of Ar exposures to acquire in K band')
p.add_argument('KArgonTime', type=int, help='exposures Time for Ar arc in K band')
p.add_argument('KFlatCount', type=int, help='number of Flats to acquire in K band')
p.add_argument('KFlatLamp', type=str, help='lamp to use for K-band flats')
p.add_argument('KFlatTime', type=int, help='exposure Time for Flats in K band')
p.add_argument('KLampsOff', type=int, help='flag indicating whether to acquire Lamps on/Lamps Off pair in K band')
p.add_argument('Shutdown', type=int, help='flag whether to shut down MOSFIRE after completion')

# The following set of params is repeated N times (once per mask):
# p.add_argument('MaskPathN', type=str, help='path to mask N .xml file')
# p.add_argument('YstatusN ', type=bool, help='calibrate mask N in Y band?')
# p.add_argument('JstatusN ', type=bool, help='calibrate mask N in J band?')
# p.add_argument('HstatusN ', type=bool, help='calibrate mask N in H band?')
# p.add_argument('KstatusN ', type=bool, help='calibrate mask N in K band?')
p.add_argument('masks', nargs='+',
               help='Mask path and whether to take Y, J, H, K calibrations')

args = p.parse_args()


cfg = {'Y':
        {'flat_count': args.YFlatCount,
         'flat_exptime': args.YFlatTime,
         'flatoff_count': args.YFlatCount if args.YLampsOff is 1 else 0,
         'ne_arc_exptime': args.YNeonTime,
         'ne_arc_count': args.YNeonCount,
         'ar_arc_exptime': args.YArgonTime,
         'ar_arc_count': args.YArgonCount,
        },
       'J':
        {'flat_count': args.JFlatCount,
         'flat_exptime': args.JFlatTime,
         'flatoff_count': args.JFlatCount if args.JLampsOff is 1 else 0,
         'ne_arc_exptime': args.JNeonTime,
         'ne_arc_count': args.JNeonCount,
         'ar_arc_exptime': args.JArgonTime,
         'ar_arc_count': args.JArgonCount,
        },
       'H':
        {'flat_count': args.HFlatCount,
         'flat_exptime': args.HFlatTime,
         'flatoff_count': args.HFlatCount if args.HLampsOff is 1 else 0,
         'ne_arc_exptime': args.HNeonTime,
         'ne_arc_count': args.HNeonCount,
         'ar_arc_exptime': args.HArgonTime,
         'ar_arc_count': args.HArgonCount,
        },
       'K':
        {'flat_count': args.KFlatCount,
         'flat_exptime': args.KFlatTime,
         'flatoff_count': args.KFlatCount if args.KLampsOff is 1 else 0,
         'ne_arc_exptime': args.KNeonTime,
         'ne_arc_count': args.KNeonCount,
         'ar_arc_exptime': args.KArgonTime,
         'ar_arc_count': args.KArgonCount,
        },
       'J2':
        {'flat_count': args.J2FlatCount,
         'flat_exptime': args.J2FlatTime,
         'flatoff_count': args.J2FlatCount if args.J2LampsOff is 1 else 0,
         'ne_arc_exptime': args.J2NeonTime,
         'ne_arc_count': args.J2NeonCount,
         'ar_arc_exptime': args.J2ArgonTime,
         'ar_arc_count': args.J2ArgonCount,
        },
      }

assert len(args.masks) % 5 == 0

masks = dict()
for masknumber in range(int(len(args.masks) / 5)):
    maskfile = args.masks[masknumber*5]
    masks[maskfile] = list()
    for filtno,filt in enumerate(['Y', 'J', 'H', 'K']):
        idx = masknumber*5 + filtno + 1
        if args.masks[idx] == '1':
            masks[maskfile].append(filt)

log.info(f'mosfireTakeMaskCalibrationData started')
log.info('Configuration:')
for filt in cfg.keys():
    log.info(f"{filt}: {cfg[filt]}")
log.info('Masks:')
for maskname in masks.keys():
    log.info(f"{maskname}: {masks[maskname]}")

if args.Shutdown == 1:
    log.info(f"Shutdown when done requested")

from instruments.mosfire.calibration import take_all_calibrations
log.info('Taking calibrations')
take_all_calibrations(masks, config=cfg)

if args.Shutdown == 1:
    from instruments.mosfire.core import end_of_night_shutdown
    log.info('Performing end of night shutdown')
    end_of_night_shutdown()
