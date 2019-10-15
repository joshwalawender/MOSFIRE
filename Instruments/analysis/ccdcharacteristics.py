#!/usr/env/python

## Import General Tools
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy import stats
from astropy.modeling import models, fitting
import ccdproc

from .core import *
from .. import KeckData, KeckDataList


def determine_read_noise(input, master_bias=None, clippingsigma=5, clippingiters=3, trimpix=0):
    '''
    Determine read noise from either a set of bias frames or from a single bias
    frame and a master bias.
    '''
    log.info(f'Determining read noise')
    if issubclass(type(input), KeckData)\
        and issubclass(type(master_bias), KeckData):
        bias0 = input
    elif type(input) == KeckDataList:
        log.info(f'  Checking that all inputs are BIAS frames')
        biases = KeckDataList([kd for kd in input.frames if kd.type() == 'BIAS'])
        log.info(f'  Found {biases.len} biases')
        bias0 = biases.pop()
        master_bias = make_master_bias(biases,
                                       clippingsigma=clippingsigma,
                                       clippingiters=clippingiters,
                                       trimpix=trimpix)
    else:
        raise KeckDataError(f'Input of type {type(input)} not understood')

    diff = bias0.subtract(master_bias)
    npds = len(diff.pixeldata)
    log.info(f'  Determining read noise for each of {npds} extensions')
    read_noise = []
    for i in range(npds):
        ny, nx = diff.pixeldata[i].shape
        mean, median, stddev = stats.sigma_clipped_stats(
                      diff.pixeldata[i][trimpix:ny-trimpix,trimpix:nx-trimpix],
                      sigma=clippingsigma,
                      iters=clippingiters) * u.adu
        mode = get_mode(diff.pixeldata[i])
        log.debug(f'  Bias Diff (mean, med, mode, std) = {mean.value:.1f}, '\
                  f'{median.value:.1f}, {mode:d}, {stddev.value:.2f}')

        RN = stddev / np.sqrt(1.+1./master_bias.nbiases )
        log.info(f'  Read Noise is {RN:.2f} for extension {i+1}')
        read_noise.append(RN)
    return u.Quantity(read_noise)


def determine_dark_current(input, master_bias=None,
                           clippingsigma=5, clippingiters=3, trimpix=0):
    '''
    Determine dark current from a set of dark frames and a master bias.
    '''
    log.info('Determining dark current')
    dark_frames = KeckDataList([kd for kd in input.frames if kd.type() == 'DARK'])
    log.info(f'  Found {dark_frames.len} dark frames')
    npds = len(dark_frames.frames[0].pixeldata)
    log.info(f'  Determining dark current for each of {npds} extensions')

    exptimes = []
    dark_means = []
    dark_medians = []
    
    for dark_frame in dark_frames.frames:
        exptimes.append(dark_frame.exptime())
        dark_diff = dark_frame.subtract(master_bias)
        dark_mean = [None] * npds
        dark_median = [None] * npds
        for i in range(npds):
            ny, nx = dark_diff.pixeldata[i].shape
            mean, median, stddev = stats.sigma_clipped_stats(
                          dark_diff.pixeldata[i][trimpix:ny-trimpix,trimpix:nx-trimpix],
                          sigma=clippingsigma,
                          iters=clippingiters) * u.adu
            log.debug(f'  Bias Diff (mean, med, std) = {mean.value:.1f}, '\
                      f'{median.value:.1f}, {stddev.value:.2f}')
            dark_mean[i] = mean.value
#             dark_median[i] = median.value
        dark_means.append(dark_mean)
#         dark_medians.append(dark_median)

    log.info(f'  Obtained statistics for frames with {len(set(exptimes))} '
             f'different exposure times')
    dark_means = np.array(dark_means)
#     dark_medians = np.array(dark_medians)

    # Fit Line to Dark Level to Determine Dark Current
    log.info(f"  Determining dark current from")
    exptime_ints = [int(t) for t in exptimes]
    for t in set(exptime_ints):
        log.info(f"    {exptime_ints.count(t)} {t} second darks")
    DC = [None]*npds
    line = models.Linear1D(intercept=0, slope=0)
    line.intercept.fixed = True
    fitter = fitting.LinearLSQFitter()
    for i in range(npds):
        dc_fit_mean = fitter(line, exptimes, dark_means[:,i])
#         dc_fit_median = fitter(line, exptimes, dark_medians[:,i])
        DC[i] = dc_fit_mean.slope.value * u.adu/u.second
        log.info(f'  Dark Current is {DC[i]:.3f} for extension {i+1}')
    return DC
