#!/usr/env/python

## Import General Tools
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy import stats
import ccdproc

from .. import create_log
from .. import KeckData

name = 'analysis'
log = create_log(name, loglevel='INFO')


def get_mode(input):
    '''
    Return mode of an array.  Assumes int values (ADU), so uses binsize of one.
    '''
    if type(input) == ccdproc.CCDData:
        data = input.data.ravel()
    elif type(input) == fits.HDUList:
        data = input[0].data.ravel()
    else:
        data = input
    
    bmin = np.floor(min(data)) - 1./2.
    bmax = np.ceil(max(data)) + 1./2.
    bins = np.arange(bmin,bmax,1)
    hist, bins = np.histogram(data, bins=bins)
    centers = (bins[:-1] + bins[1:]) / 2
    w = np.argmax(hist)
    mode.append( int(centers[w]) )

    return mode


def make_master_bias(kdl, clippingsigma=5, clippingiters=3, trimpix=0):
    '''
    Make master bias from a set of KeckData objects.
    '''
    if type(kdl) == list:
        kdl = KeckDataList(kdl)
    elif type(kdl) == KeckDataList:
        pass
    else:
        raise KeckDataError

    log.info('  Making master bias')
    master_bias_kd = KeckData()
    for i in range(kdl.len):
        biases = [kd.pixeldata[i] for kd in kdl.kds]
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
        log.debug(f'  Master Bias {i} (mean, med, mode, std) = {mean.value:.1f}, '\
                  f'{median.value:.1f}, {mode:d}, {stddev.value:.2f}')
        master_bias_kd.pixeldata.append(master_bias_i.data)
    return master_bias_kd


def determine_read_noise(kdl, trimpix==0):
    '''
    Determine read noise from a set of bias frames.
    '''
    log.info(f'Determining read noise')
    biases = [kd for kd in kdl.kds if kd.type() == 'BIAS']
    log.info(f'  Found {len(biases)} biases')
    bias0 = biases.pop(0)
    remaining_biases = KeckDataList(biases)

    master_bias = make_master_bias(remaining_biases)
    diff = bias0.subtract(master_bias)

