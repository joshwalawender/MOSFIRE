from pathlib import Path

import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot as plt
plt.ioff()

import numpy as np
from scipy import ndimage
from astropy.io import fits
from astropy import visualization as viz
from astropy.modeling import models, fitting

from .core import *
from .csu import slit_to_bars, physical_to_pixel, pixel_to_physical, bar_to_slit


## ------------------------------------------------------------------
##  Compare Image to Mask Design
## ------------------------------------------------------------------
def verify_mask_with_image(mask, imagefile, tolerance=2, plot=False, filtersize=7):
    log.info('Finding bar positions')
    foundbars = find_bar_positions_from_image(imagefile,
                        filtersize=filtersize, plot=plot)
    log.info('Verifying bar positions')
    barsok = list()

    diffs = {}

    for bar in range(1,93):
        found = foundbars[bar]
        if bar %2 == 0:
            slitinfo = mask.slitpos[mask.slitpos['leftBarNumber'] == bar]
            expected_mm = float(slitinfo['leftBarPositionMM'])
        else:
            slitinfo = mask.slitpos[mask.slitpos['rightBarNumber'] == bar]
            expected_mm = float(slitinfo['rightBarPositionMM'])
        expected = physical_to_pixel([[expected_mm, bar_to_slit(bar)]])[0][0][0]
        diffs[bar] = abs(found - expected)

        if not np.isclose(found, expected, atol=tolerance):
            log.warning(f'Bar {bar} out of tolerance: got {found:.1f} '
                        f'expected {expected:.1f} (difference = {diffs[bar]:.1f})')
            barsok.append(False)
        else:
            log.debug(f'Bar {bar} is within tolerance: got {found:.1f} '
                      f'expected {expected:.1f} (difference = {diffs[bar]:.1f})')
            barsok.append(True)
    if not np.all(barsok):
        log.error('Image did not match mask design')
#         raise FailedCondition('Image did not match mask design')
    else:
        log.info(f'Bars all verified within {tolerance} pixels')

    return diffs


## ------------------------------------------------------------------
##  Analyze Image to Determine Bar Positions
## ------------------------------------------------------------------
def find_bar_positions_from_image(imagefile, filtersize=5, plot=False,
                                  pixel_shim=5):
    '''Loop over all slits in the image and using the affine transformation
    determined by `fit_transforms`, select the Y pixel range over which this
    slit should be found.  Take a median filtered version of that image and
    determine the X direction gradient (derivative).  Then collapse it in
    the Y direction to form a 1D profile.
    
    Using the `find_bar_edges` method, determine the X pixel positions of
    each bar forming the slit.
    
    Convert those X pixel position to physical coordinates using the
    `pixel_to_physical` method and then call the `compare_to_csu_bar_state`
    method to determine the bar state.
    '''
    ## Get image from file
    imagefile = Path(imagefile).absolute()
    try:
        hdul = fits.open(imagefile)
        data = hdul[0].data
    except Error as e:
        log.error(e)
        raise
    # median X pixels only (preserve Y structure)
    medimage = ndimage.median_filter(data, size=(1, filtersize))
    
    bars = {}
    bars_mm = {}
    ypos = {}
    for slit in range(1,47):
        b1, b2 = slit_to_bars(slit)
        ## Determine y pixel range
        y1 = int(np.ceil((physical_to_pixel(np.array([(4.0, slit+0.5)])))[0][0][1])) + pixel_shim
        y2 = int(np.floor((physical_to_pixel(np.array([(270.4, slit-0.5)])))[0][0][1])) - pixel_shim
        ypos[b1] = [y1, y2]
        ypos[b2] = [y1, y2]
        gradx = np.gradient(medimage[y1:y2,:], axis=1)
        horizontal_profile = np.sum(gradx, axis=0)
        try:
            bars[b1], bars[b2] = find_bar_edges(horizontal_profile)
            ypix_estimate = (y1+y2)/2
            bars_mm[b1] = pixel_to_physical(np.array([(bars[b1], ypix_estimate)]))[0][0][0]
            bars_mm[b2] = pixel_to_physical(np.array([(bars[b2], ypix_estimate)]))[0][0][0]
        except:
            print(f'Unable to fit bars: {b1}, {b2}')

    # Generate plot if called for
    if plot is True:
        plotfile = imagefile.with_name(f"{imagefile.stem}.png")
        log.info(f'Creating PNG image {plotfile}')
        if plotfile.exists(): plotfile.unlink()
        plt.figure(figsize=(16,16), dpi=300)
        norm = viz.ImageNormalize(data, interval=viz.PercentileInterval(99.9),
                                  stretch=viz.LinearStretch())
        plt.imshow(data, norm=norm, origin='lower', cmap='Greys')


        for bar in bars.keys():
#             plt.plot([0,2048], [ypos[bar][0], ypos[bar][0]], 'r-', alpha=0.1)
#             plt.plot([0,2048], [ypos[bar][1], ypos[bar][1]], 'r-', alpha=0.1)

            mms = np.linspace(4,270.4,2)
            slit = bar_to_slit(bar)
            pix = np.array([(physical_to_pixel(np.array([(mm, slit+0.5)])))[0][0] for mm in mms])
            plt.plot(pix.transpose()[0], pix.transpose()[1], 'g-', alpha=0.5)

            plt.plot([bars[bar],bars[bar]], ypos[bar], 'r-', alpha=0.75)
            offset = {0: -20, 1:+20}[bar % 2]
            plt.text(bars[bar]+offset, np.mean(ypos[bar]), bar,
                     fontsize=8, color='r', alpha=0.75,
                     horizontalalignment='center', verticalalignment='center')
        plt.savefig(str(plotfile), bbox_inches='tight')

    return bars, bars_mm


def find_bar_edges(horizontal_profile):
    '''Given a 1D profile, dertermime the X position of each bar that forms
    a single slit.  The slit edges are found by fitting one positive and
    one negative gaussian function to the profile.
    '''
    fitter = fitting.LevMarLSQFitter()

    amp1_est = horizontal_profile[horizontal_profile == min(horizontal_profile)]
    mean1_est = np.argmin(horizontal_profile)
    amp2_est = horizontal_profile[horizontal_profile == max(horizontal_profile)]
    mean2_est = np.argmax(horizontal_profile)

    g_init1 = models.Gaussian1D(amplitude=amp1_est, mean=mean1_est, stddev=2.)
    g_init1.amplitude.max = 0
    g_init2 = models.Gaussian1D(amplitude=amp2_est, mean=mean2_est, stddev=2.)
    g_init2.amplitude.min = 0

    model = g_init1 + g_init2
    fit = fitter(model, range(0,horizontal_profile.shape[0]), horizontal_profile)

    # Check Validity of Fit
    if abs(fit.stddev_0.value) < 3 and abs(fit.stddev_1.value) < 3\
       and fit.amplitude_0.value < -1 and fit.amplitude_1.value > 1\
       and fit.mean_0.value > fit.mean_1.value:
        x1 = fit.mean_0.value
        x2 = fit.mean_1.value
    else:
        x1 = None
        x2 = None
    
    return (x1, x2)


def find_individual_slits(imagefile, filtersize=3, plot=True):
    '''Analyze an image of a mask where very slit is separated (all slits have
    length ~7 arcsec).  Determine the center of each slit.  Used to fit or
    verify the transform between slit mm and pixels.
    '''
    foundbars = find_bar_positions_from_image(imagefile,
                        filtersize=filtersize, plot=plot)

    
    for slit in range(1,47,1):
        leftbar, rightbar = slit_to_bars(slit)
        xpix = np.mean( [foundbars[leftbar], foundbars[rightbar]] )
    
    