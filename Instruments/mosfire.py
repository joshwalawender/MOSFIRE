#!/usr/env/python

## Import General Tools
import sys
from pathlib import Path
import logging
import yaml

from datetime import datetime as dt
from time import sleep
import numpy as np
import subprocess
import xml.etree.ElementTree as ET

from astropy.io import fits

from Instruments import connect_to_ktl, create_log




##-------------------------------------------------------------------------
## MOSFIRE Properties
##-------------------------------------------------------------------------
name = 'MOSFIRE'
serviceNames = ['mosfire']
modes = ['Dark-Imaging', 'Dark-Spectroscopy', 'Imaging', 'Spectroscopy']
filters = ['Y', 'J', 'H', 'K', 'J2', 'J3', 'NB']
allowed_sampmodes = [2, 3]

# Load default CSU coordinate transformations
filepath = Path(__file__).parent
with open(filepath.joinpath('MOSFIRE_transforms.txt'), 'r') as FO:
    Aphysical_to_pixel, Apixel_to_physical = yaml.safe_load(FO.read())
Aphysical_to_pixel = np.array(Aphysical_to_pixel)
Apixel_to_physical = np.array(Apixel_to_physical)

log = create_log(name)
services = connect_to_ktl(name, serviceNames)


##-------------------------------------------------------------------------
## Define Common Functions
##-------------------------------------------------------------------------
def get(service, keyword, mode=str):
    """Generic function to get a keyword value.  Converts it to the specified
    mode and does some simple parsing of true and false strings.
    """
    log.debug(f'Querying {service} for {keyword}')
    if services == {}:
        return None
    assert mode in [str, float, int, bool]
    kwresult = services[service][keyword].read()
    log.debug(f'  Got result: "{kwresult}"')

    # Handle string versions of true and false
    if mode is bool:
        if kwresult.strip().lower() == 'false':
            result = False
        elif kwresult.strip().lower() == 'true':
            result = True
        log.debug(f'  Parsed to boolean: {result}')
        return result
    # Convert result to requested type
    try:
        result = mode(kwresult)
        log.debug(f'  Parsed to {mode}: {result}')
        return result
    except ValueError:
        log.warning(f'Failed to parse {kwresult} as {mode}, returning string')
        return kwresult


def set(service, keyword, value, wait=True):
    """Generic function to set a keyword value.
    """
    log.debug(f'Setting {service}.{keyword} to "{value}" (wait={wait})')
    if services == {}:
        return None
    services[service][keyword].write(value, wait=wait)
    log.debug(f'  Done.')


##-------------------------------------------------------------------------
## MOSFIRE Functions
##-------------------------------------------------------------------------
def get_mode():
    obsmode = get('mosfire', 'OBSMODE')
    return obsmode.split('-')


def get_filter():
    filter = get('mosfire', 'FILTER')
    return filter


def is_dark():
    filter = get_filter()
    return filter == 'Dark'


def set_mode(filter, mode):
    if not mode in modes:
        log.error(f"Mode: {mode} is unknown")
    elif not filter in filters:
        log.error(f"Filter: {filter} is unknown")
    else:
        log.info(f"Setting mode to {filter}-{mode}")
    modestr = f"{filter}-{mode}"
    set('mosfire', 'OBSMODE', modestr, wait=True)
    if get_mode() != modestr:
        log.error(f'Mode "{modestr}" not reached.  Current mode: {get_mode()}')


def go_dark():
    # See darkeff instead!!!
    if is_dark():
        log.info('Already Dark (mode = {get_mode()})')
        return True
    log.info('Going dark')
    current = get_mode()
    setmode('Dark', current[1])
    return is_dark()


def grating_shim_ok():
    return get('mosfire', 'MGSSTAT') == 'OK':


def grating_turret_ok():
    return get('mosfire', 'MGTSTAT') == 'OK':


def grating_ok():
    return get('mosfire', 'GRATSTAT') == 'OK':


def filter1_ok():
    return get('mosfire', 'MF1STAT') == 'OK':


def filter2_ok():
    return get('mosfire', 'MF2STAT') == 'OK':


def filters_ok():
    return get('mosfire', 'FILTSTAT') == 'OK':


def fcs_ok():
    return get('mosfire', 'FCSSTAT') == 'OK':


def pupil_rotator_ok():
    return get('mosfire', 'MPRSTAT') == 'OK':


def trapdoor_ok():
    return dustcover_ok()


def dustcover_ok():
    return get('mosfire', 'MDCSTAT') == 'OK':


def check_mechanisms():
    mechs = ['filter1', 'filter2', 'fcs', 'grating_shim', 'grating_turret',
             'pupil_rotator', 'trapdoor']
    for mech in mechs:
        statusfn = getattr(sys.modules[__name__], f'{mech}_ok')
        ok = statusfn()
        if ok is False:
            log.error(f'{mech} status is not ok')
            log.error(f'Please address the problem, then re-run the checkout.')
            return False
    return True


##-------------------------------------------------------------------------
## Read Mask Design Files
##-------------------------------------------------------------------------
def read_maskfile(xml):
    xmlfile = Path(xml)
    if xmlfile.exists():
        tree = ET.parse(xmlfile)
        root = tree.getroot()
    else:
        try:
            root = ET.fromstring(xml)
        except:
            print(f'Could not parse {xml} as file or XML string')
            raise
    mask = {}
    for child in root:
        if child.tag == 'maskDescription':
            mask['maskDescription'] = child.attrib
        elif child.tag == 'mascgenArguments':
            mask['mascgenArguments'] = {}
            for el in child:
                if el.attrib == {}:
                    mask['mascgenArguments'][el.tag] = (el.text).strip()
                else:
                    print(el.tag, el.attrib)
                    mask['mascgenArguments'][el.tag] = el.attrib
        else:
            mask[child.tag] = [el.attrib for el in child.getchildren()]

    return mask


## ------------------------------------------------------------------
##  Coordinate Transformation Utilities
## ------------------------------------------------------------------
def slit_to_bars(slit):
    '''Given a slit number (1-46), return the two bar numbers associated
    with that slit.
    '''
    return (slit*2-1, slit*2)


def bar_to_slit(bar):
    '''Given a bar number, retun the slit associated with that bar.
    '''
    return int((bar+1)/2)


def pad(x):
    '''Pad array for affine transformation.
    '''
    return np.hstack([x, np.ones((x.shape[0], 1))])


def unpad(x):
    '''Unpad array for affine transformation.
    '''
    return x[:,:-1]


def fit_transforms(pixels, physical):
    '''Given a set of pixel coordinates (X, Y) and a set of physical
    coordinates (mm, slit), fit the affine transformations (forward and
    backward) to convert between the two coordinate systems.
    
    '''
    pixels = np.array(pixels)
    physical = np.array(physical)
    assert pixels.shape[1] == 2
    assert physical.shape[1] == 2
    assert pixels.shape[0] == physical.shape[0]

    # Pad the data with ones, so that our transformation can do translations too
    n = pixels.shape[0]
    pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
    unpad = lambda x: x[:,:-1]
    X = pad(pixels)
    Y = pad(physical)

    # Solve the least squares problem X * A = Y
    # to find our transformation matrix A
    A, res, rank, s = np.linalg.lstsq(X, Y, rcond=None)
    Ainv, res, rank, s = np.linalg.lstsq(Y, X, rcond=None)
    A[np.abs(A) < 1e-10] = 0
    Ainv[np.abs(A) < 1e-10] = 0
    Apixel_to_physical = A
    Aphysical_to_pixel = Ainv
    return Apixel_to_physical, Aphysical_to_pixel


def pixel_to_physical(x):
    '''Using the affine transformation determined by `fit_transforms`,
    convert a set of pixel coordinates (X, Y) to physical coordinates (mm,
    slit).
    '''
    x = np.array(x)
    result = unpad(np.dot(pad(x), Apixel_to_physical))
    return result


def physical_to_pixel(x):
    '''Using the affine transformation determined by `fit_transforms`,
    convert a set of physical coordinates (mm, slit) to pixel coordinates
    (X, Y).
    '''
    x = np.array(x)
    result = unpad(np.dot(pad(x), Aphysical_to_pixel))
    return result


## Set up initial transforms for pixel and physical space
# pixelfile = filepath.joinpath('MOSFIRE_pixels.txt')
# with open(pixelfile, 'r') as FO:
#     contents = FO.read()
#     pixels = yaml.safe_load(contents)
# physicalfile = filepath.joinpath('MOSFIRE_physical.txt')
# with open(physicalfile, 'r') as FO:
#     contents = FO.read()
#     physical = yaml.safe_load(contents)
# Apixel_to_physical, Aphysical_to_pixel = fit_transforms(pixels, physical)
## Convert from numpy arrays to list for simpler YAML
# Apixel_to_physical = [ [float(val) for val in line] for line in Apixel_to_physical]
# Aphysical_to_pixel = [ [float(val) for val in line] for line in Aphysical_to_pixel]
# with open('MOSFIRE_transforms.txt', 'w') as FO:
#     FO.write(yaml.dump([Aphysical_to_pixel, Apixel_to_physical]))


## ------------------------------------------------------------------
##  Analyze Image to Determine Bar Positions
## ------------------------------------------------------------------
def analyze_mask_image(imagefile, filtersize=7):
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
    imagefile = Path(imagefile).abspath
    try:
        hdul = fits.open(imagefile)
        data = hdul[0].data
    except Error as e:
        log.error(e)
        raise
    ## Get image from ginga
#     try:
#         channel = self.fv.get_channel(self.chname)
#         image = channel.get_current_image()
#         data = image._get_data()
#     except:
#         print('Failed to load image data')
#         return

    # median X pixels only (preserve Y structure)
    medimage = ndimage.median_filter(data, size=(1, filtersize))
    
    bars_analysis = {}
    state_analysis = {}
    for slit in range(1,47):
        b1, b2 = slit_to_bars(slit)
        ## Determine y pixel range
        y1 = int(np.ceil((physical_to_pixel(np.array([(4.0, slit+0.5)])))[0][1]))
        y2 = int(np.floor((physical_to_pixel(np.array([(270.4, slit-0.5)])))[0][1]))
        gradx = np.gradient(medimage[y1:y2,:], axis=1)
        horizontal_profile = np.sum(gradx, axis=0)
        x1, x2 = self.find_bar_edges(horizontal_profile)
        if x1 is None:
            self.bars_analysis[b1] = None
            self.state_analysis[b1] = 'UNKNOWN'
        else:
            mm1 = (self.pixel_to_physical(np.array([(x1, (y1+y2)/2.)])))[0][0]
            self.bars_analysis[b1] = mm1
            self.state_analysis[b1] = 'ANALYZED'
        if x2 is None:
            self.bars_analysis[b2] = None
            self.state_analysis[b2] = 'UNKNOWN'
        else:
            mm2 = (self.pixel_to_physical(np.array([(x2, (y1+y2)/2.)])))[0][0]
            self.bars_analysis[b2] = mm2
            self.state_analysis[b2] = 'ANALYZED'
        testx1 = self.physical_to_pixel([[mm2, slit]])
        print(slit, x2, x1, x1-x2, mm2, mm1, testx1)
#         self.compare_to_csu_bar_state()


def find_bar_edges(self, horizontal_profile):
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



##-------------------------------------------------------------------------
## MOSFIRE Quick Checkout
##-------------------------------------------------------------------------
def checkout_quick(interactive=True):
    '''
    * Confirm the physical drive angle. It should not be within 10 degrees of a
         multiple of 180 degrees
    * Start the observing software as moseng or the account for the night
    * Check that the dark filter is selected. If not select it
    * Check mechanism status: If any of the mechanisms have a big red X on it,
         you will need to home mechanisms. Note, if filter wheel is at the home
         position, Status will be "OK," position will be "HOME", target will be
         "unknown", and there will still be a big red X.
    * Acquire an exposure
    * Inspect the dark image
    * Create an 2.7x46 long slit and image it, verify bar positions
    * Create an 0.7x46 long slit and image it, verify bar positions
    * With the hatch closed change the observing mode to J-imaging, verify
         mechanisms are ok
    * Quick Dark
    '''
    intromsg = 'This script will do a quick checkout of MOSFIRE.  It should '\
               'take about ?? minutes to complete.  Please confirm that you '\
               'have started the MOSFIRE software AND that the instrument '\
               'rotator is not within 10 degrees of a multiple of 180 degrees.'
    if interactive:
        log.info(intromsg)
        log.info()
        print('Proceed? [y]')
        proceed = input('Continue? [y]')
        if proceed.lower() not in ['y', 'yes', 'ok', '']:
            log.info('Exiting script.')
            return False
        log.info('Executing quick checkout script.')
    
    # Verify that the instrument is "dark"
    if not is_dark():
        go_dark()
    check_mechanisms()
    # Verify Dark Image
    # Create an 2.7x46 long slit and image it, verify bar positions
    # Create an 0.7x46 long slit and image it, verify bar positions
    # Change the observing mode to J-imaging, verify mechanisms
    # Quick Dark
