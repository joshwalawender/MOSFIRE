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


def make_master_bias(kds, clippingsigma=5, clippingiters=3, trimpix=0):
    '''
    Make master bias from a set of KeckData objects.
    '''
    # Assume all input object have the same number of pixeldata arrays
    pixeldata_lengths = set([len(kd.pixeldata) for kd in kds])
    assert len( pixeldata_lengths ) == 1
    npixeldata = pixeldata_lengths.pop()

    log.info('  Making master bias')
    master_pds = []
    for i in range(npixeldata):
        biases = [kd.pixeldata[i] for kd in kds]
        master_bias = ccdproc.combine(biases, combine='average',
            sigma_clip=True,
            sigma_clip_low_thresh=clippingsigma,
            sigma_clip_high_thresh=clippingsigma)
        ny, nx = master_bias.data.shape
        mean, median, stddev = stats.sigma_clipped_stats(
            master_bias.data[trimpix:ny-trimpix,trimpix:nx-trimpix],
            sigma=clippingsigma,
            iters=clippingiters) * u.adu
        mode = get_mode(master_bias.data)
        log.debug(f'  Master Bias (mean, med, mode, std) = {mean.value:.1f}, '\
                  f'{median.value:.1f}, {mode:d}, {stddev.value:.2f}')
        master_pds.append(master_bias.data)



def determine_read_noise(kds, trimpix==0):
    '''
    Determine read noise from a set of bias frames.
    '''
    log.info(f'Determining read noise')
    biases = [kd for kd in kds if kd.type() == 'BIAS']
    log.info(f'  Found {len(biases)} biases')
    for i,bias in enumerate(biases):
        if i == 0:
            ny, nx = kd.pixeldata.shape
            mean, median, stddev = stats.sigma_clipped_stats(
                                         kd.pixeldata[buf:ny-buf,buf:nx-buf],
                                         sigma=args.clippingsigma,
                                         iters=args.clippingiters) * u.adu
            mode = get_mode(bias0)
            log.debug(f'  Bias (mean, med, mode, std) = {mean.value:.1f}, '
                      f'{median.value:.1f}, {mode:d}, {stddev.value:.2f}')
