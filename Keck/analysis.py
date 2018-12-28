import argparse
import logging
from glob import glob

import numpy as np
from astropy import units as u
from astropy.table import Table, Column
from astropy.modeling import models, fitting
from astropy import stats
from astropy.io import fits

import ccdproc

## Suppress astropy log
from astropy import log
log.setLevel('ERROR')
# log.disable_warnings_logging()

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.size'] = 10
import matplotlib.pyplot as plt


##-------------------------------------------------------------------------
## MEF
##-------------------------------------------------------------------------
class MEF(object):
    



##-------------------------------------------------------------------------
## get_mode
##-------------------------------------------------------------------------
def get_mode(im):
    '''
    Return mode of image.  Assumes int values (ADU), so uses binsize of one.
    '''
    bmin = np.floor(min(im.data.ravel())) - 1./2.
    bmax = np.ceil(max(im.data.ravel())) + 1./2.
    bins = np.arange(bmin,bmax,1)
    hist, bins = np.histogram(im.data.ravel(), bins=bins)
    centers = (bins[:-1] + bins[1:]) / 2
    w = np.argmax(hist)
    mode = int(centers[w])
    return mode


##-------------------------------------------------------------------------
## 
##-------------------------------------------------------------------------
def read_noise(files):
    '''Given a list of bias frame files (single or multi extension), measure
    the noise in the bias frames to determine the read noise.
    
    This assumes that each chip (or amplifier) in the detector array has its
    own FITS extension and that the units are ADU.
    '''
    ccds = []
    for i,file in enumerate(files):
        ccds_for_file = []
        hdul = fits.open(file)
        for hdu in hdul:
            if type(hdu) in [fits.PrimaryHDU, fits.ImageHDU]:
                ccds_for_file.append(ccdproc.CCDData(data=hdu.data,
                                     meta=hdu.header, unit=u.adu))
        ccds.append(ccds_for_file)
        if i > 0:
            assert len(ccds[i]) == len(ccds[i-1])
    
    
    