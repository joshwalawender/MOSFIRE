#!/usr/env/python

## Import General Tools
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy import stats
import ccdproc

from .. import create_log
from .. import KeckData, KeckDataList

name = 'analysis'
log = create_log(name, loglevel='INFO')


def get_mode(input):
    '''
    Return mode of an array, HDUList, or CCDData.  Assumes int values (ADU),
    so uses binsize of one.
    '''
    if type(input) == ccdproc.CCDData:
        data = input.data.ravel()
    elif type(input) == fits.HDUList:
        data = input[0].data.ravel()
    else:
        data = input.ravel()
    
    bmin = np.floor(min(data)) - 1./2.
    bmax = np.ceil(max(data)) + 1./2.
    bins = np.arange(bmin,bmax,1)
    hist, bins = np.histogram(data, bins=bins)
    centers = (bins[:-1] + bins[1:]) / 2
    w = np.argmax(hist)
    mode = int(centers[w])

    return mode


def make_master_bias(kdl, clippingsigma=5, clippingiters=3, trimpix=0):
    '''
    Make master bias from a set of KeckData objects.  Input should be either
    a list of KeckData objects, a list of file paths, or a KeckDataList object.
    '''
    if type(kdl) == list:
        kdl = KeckDataList(kdl)
    elif type(kdl) == KeckDataList:
        pass
    else:
        raise KeckDataError

    log.info(f'Making master bias from {kdl.len} frames')
    master_bias_kd = kdl.kdtype()

    npds = len(kdl.frames[0].pixeldata)
    log.info(f'Making master bias for each of {npds} extensions')
    for i in range(npds):
        biases = [kd.pixeldata[i] for kd in kdl.frames]
        master_bias_i = ccdproc.combine(biases, combine='average',
            sigma_clip=True,
            sigma_clip_low_thresh=clippingsigma,
            sigma_clip_high_thresh=clippingsigma)
        ny, nx = master_bias_i.data.shape
        mean, median, stddev = stats.sigma_clipped_stats(
            master_bias_i.data[trimpix:ny-trimpix,trimpix:nx-trimpix],
            sigma=clippingsigma,
            iters=clippingiters) * u.adu
        mode = get_mode(master_bias_i.data)
        log.debug(f'  Master Bias {i} (mean, med, mode, std) = {mean.value:.1f}, '
                  f'{median.value:.1f}, {mode:d}, {stddev.value:.2f}')
        master_bias_kd.pixeldata.append(master_bias_i)
    master_bias_kd.nbiases = kdl.len
    log.info('  Done')
    return master_bias_kd
