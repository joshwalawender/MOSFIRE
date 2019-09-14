from .core import *


## ------------------------------------------------------------------
##  Analyze Image to Determine Bar Positions
## ------------------------------------------------------------------
def analyze_mask_image(imagefile, filtersize=7, plot=False):
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
    ypos = {}
    for slit in range(1,47):
        b1, b2 = slit_to_bars(slit)
        ## Determine y pixel range
        y1 = int(np.ceil((physical_to_pixel(np.array([(4.0, slit+0.5)])))[0][1]))
        y2 = int(np.floor((physical_to_pixel(np.array([(270.4, slit-0.5)])))[0][1]))
        ypos[b1] = [y1, y2]
        ypos[b2] = [y1, y2]
        gradx = np.gradient(medimage[y1:y2,:], axis=1)
        horizontal_profile = np.sum(gradx, axis=0)
        bars[b1], bars[b2] = find_bar_edges(horizontal_profile)

    # Generate plot if called for
    if plot is True:
        plotfile = imagefile.with_name(f"{imagefile.name}.png")
        if plotfile.exists(): plotfile.unlink()
        plt.figure(figsize=(16,16))
        norm = viz.ImageNormalize(data, interval=viz.PercentileInterval(99),
                                  stretch=viz.LinearStretch())
        plt.imshow(data, norm=norm, origin='lower', cmap='Greys')
        for bar in bars.keys():
            plt.plot([0,2048], [ypos[bar][0], ypos[bar][0]], 'r-', alpha=0.1)
            plt.plot([0,2048], [ypos[bar][1], ypos[bar][1]], 'r-', alpha=0.1)
            plt.plot(bars[bar], np.mean(ypos[bar]), 'rx', alpha=0.5)
        plt.savefig(str(plotfile))

    return bars


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
