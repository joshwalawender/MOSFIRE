from .core import *
from .cals import *
from .detector import *
from .dewar import *
from .expo import *
from .iodine import *
from .mechs import *


# -----------------------------------------------------------------------------
# Take Data for Detector Characterization
# -----------------------------------------------------------------------------
def take_characterization_data(noflats=True, nframes=5, binning='2x1',
          darktimes=[60,120,300,600,900],
          flattimes=[5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 80, 100, 140, 180],
          ):
    assert enclosure_safe() is True

    set_binning(binning)

    # Take flats
    set_covers('open')
    set('hires', 'xdcover', 'closed', wait=True)
    set_lamp('quartz1')
    set_lamp_filter('clear')
    set_filters('clear', 'clear')
    set_echang(0)
    set_xdang(0)
    for flattime in flattimes:
        set_obstype('IntFlat')
        set_exptime(flattime)
        take_exposure(nexp=nframes)
    set_lamp('none')
    set_lamp_filter('ng3')

    # Take Biases and Darks
    set_covers('closed')
    set_obstype('Bias')
    set_exptime(0)
    take_exposure(nexp=nframes)
    for darktime in darktimes:
        set_obstype('Bias')
        set_exptime(0)
        take_exposure(nexp=nframes)
        set_obstype('Dark')
        set_exptime(darktime)
        take_exposure(nexp=nframes)


# -----------------------------------------------------------------------------
# Calibrate Cross Disperser
# -----------------------------------------------------------------------------
def calibrate_cd():
    # Check that lights are off and foor is closed in the HIRES enclosure
    if enclosure_safe() is False:
        log.error('Enclosure may be occupied, halting script.')
        return False

    mode = collimator()
    print(f'Calibrating {mode} cross disperser.')
    proceed = input('Continue? [y]')
    if proceed.lower() not in ['y', 'yes', 'ok', '']:
        return

    # modify -s hiccd outfile = $OUTFILE
    outfile = {'red': 'rzero', 'blue': 'uvzero'}[mode]
    set('hiccd', 'OUTFILE', outfile)
    # modify -s hiccd todisk=f
    set('hiccd', 'TODISK', 'false')
    # modify -s hiccd ttime = $TTIME
    ttime = {'red': 8, 'blue': 1}[mode]
    set_exptime(ttime)
    # modify -s hiccd pane=2048,1968,2048,160
    set('hiccd', 'pane', (2048,1968,2048,160))
    # modify -s hiccd binning=1,1
    set_binning('1x1')
    # modify -s hiccd ampmode=single:B
    set('hiccd', 'ampmode', 'single:B')
    # modify -s hiccd postpix=80
    set('hiccd', 'postpix', 80)

    # modify -s hires xdraw = -10000
    set_xdraw(-10000)
    open_covers()
    set_obstype('IntFlat')

    # -------------------------------------------------------------------------
    # Loop until done
    done = False
    while not done:
        # -------------------------------------------------------------------------
        # prep for calibration images
        # modify -s hires lfilname=ng3 nowait
        set_lamp_filter('ng3', wait=False)
        # modify -s hires lampname=quartz2 nowait
        set_lamp('quartz2', wait=False)
        # modify -s hires deckname=D5 nowait
        set_decker('D5', wait=False)
        # modify -s hires fil1name=clear nowait
        # modify -s hires fil2name=clear nowait
        set_filters('clear', 'clear', wait=False)
        # modify -s hires cofname=DR00mm nowait
        cofname = {'red': 'DR00mm', 'blue': 'DB00mm'}[mode]
        set('hires', 'COFNAME', cofname, wait=False)
        # modify -s hires echname=blaze nowait
        set('hires', 'ECHNAME', 'blaze', wait=False)
        # modify -s hires slitname=opened nowait
        open_slit(wait=False)
        # modify -s hires xdname=0-order nowait
        set('hires', 'XDNAME', '0-order', wait=False)

        # modify -s hires lfilname=ng3 wait
        set_lamp_filter('ng3')
        # modify -s hires lampname=quartz2 wait
        set_lamp('quartz2')
        # modify -s hires deckname=D5 wait
        set_decker('D5')
        # modify -s hires fil1name=clear wait
        # modify -s hires fil2name=clear wait
        set_filters('clear', 'clear')
        # modify -s hires coll=red wait
        # modify -s hires cofname=DR00mm wait
        set('hires', 'COFNAME', cofname)
        # modify -s hires echname=blaze wait
        set('hires', 'ECHNAME', 'blaze')
        # modify -s hires slitname=opened wait
        open_slit()

        set_xdraw(-10000)
        take_exposure()
    
        # Analyze Result
        hdul = fits.open(Path(get('hiccd', 'outdir')).joinpath('backup.fits'))
        assert hdul[0].data is None
        assert hdul[1].data.shape == (160, 2140)
        assert len(hdul) == 2
    
        row = 80
        rng = 20
        xpix = [x+1 for x in range(2140)]
        fine_xpix = [(x+1)/10 for x in range(21400)]
        y = list(np.mean(hdul[1].data[row-rng:row+rng,:], axis=0))
        maxy = max(y[10:-10])
        maxx = y.index(maxy)

        g_init = models.Const1D(1000)\
                 + models.Gaussian1D(amplitude=6000, mean=maxx, stddev=2.)
        g_init.amplitude_1.bounds = (0, None)
        fit_g = fitting.LevMarLSQFitter()
        g = fit_g(g_init, xpix, y)
        zero_pos = g.mean_1.value
        background = g.amplitude_0.value
        peak = g.amplitude_0.value+g.amplitude_1.value
        print(f"Position of Zero Order = {zero_pos:.1f} pix")
        print(f"Background Level = {background:.1f} ADU")
        print(f"Peak Value = {peak:.1f} ADU")
        print(f"Width of zero order = {g.stddev_1.value:.1f} pix")
        print()
        print(f"Close plot window to proceed ...")
    
        plt.figure(figsize=(12,5))
        plt.subplot(1,2,1)
        plt.title(f"Position of Zero Order = {zero_pos:.1f}")
        plt.plot(xpix, y, 'k-', drawstyle='steps-mid', alpha=0.7)
        plt.plot(xpix, g(xpix), 'g-', alpha=0.7)
        plt.ylim(background*0.7, peak*1.1)
        plt.xlabel('X Pix')
        plt.ylabel('Value (ADU)')
        plt.subplot(1,2,2)
        plt.title(f"Position of Zero Order = {zero_pos:.1f}")
        plt.plot(xpix, y, 'k-', drawstyle='steps-mid', alpha=0.7)
        plt.plot(fine_xpix, g(fine_xpix), 'g-', alpha=0.7)
        plt.plot([zero_pos, zero_pos], [0,peak*1.1], 'g-', alpha=0.4)
        plt.xlim(zero_pos-20,zero_pos+20)
        plt.ylim(background*0.7, peak*1.1)
        plt.xlabel('X Pix')
        plt.show()
    
        # Running xdchange
        xdchangemode = {'red': 'red', 'blue': 'uv'}[mode]
        xdchange_cmd = ['xdchange', xdchangemode, f"{g.mean_1.value:.1f}", 
                        f"{xdraw():d}"]
        print(f"Run on hiresserver: {' '.join(xdchange_cmd)}")
        
#         ssh_cmd = ['xterm', '-e', 'ssh', 'hiresserver', 
#         print(f'Running: {" ".join(ssh_cmd)}')
#         subprocess.call(ssh_cmd)

        proceed = ''
        while proceed.lower() not in ['n', 'no', 'y', 'yes']:
            proceed = input('Take another image? [y]')
            if proceed.lower() in ['n', 'no']:
                print('Done with calibration, proceeding with cleanup.')
                done = True
            elif proceed.lower() in ['y', 'yes', '']:
                print('Taking new calibration image.')
                proceed = 'y'
            else:
                print(f'"{proceed}" not understood.')


    ## Cleanup from oneamp.low
    # modify -s hiccd ampmode=single:B
    set('hiccd', 'ampmode', 'single:B')
    # modify -s hiccd ccdgain = low
    set_gain('low')
    # modify -s hiccd postline=0
    set('hiccd', 'postline', 0)
    # modify -s hiccd postpix=80
    set('hiccd', 'postpix', 80)
    # modify -s hiccd preline=0
    set('hiccd', 'preline', 00)
    # modify -s hiccd pane=0,0,6144,4096
    set('hiccd', 'pane', (0,0,6144,4096))
    # modify -s hiccd binning=2,1
    set_binning('2x1')

    # modify -s hiccd outfile=hires
    set('hiccd', 'OUTFILE', 'hires')

    set_lamp('none')

