import numpy as np
from scipy.interpolate import CubicSpline
from typing import Tuple
from numpy.typing import NDArray

def derive_reference_psd(psd: NDArray) -> NDArray:
    return np.median(psd, axis=0)

def remove_frequency_gain_variation(psd: NDArray, psd_ref: NDArray) -> NDArray:
    """Removes the frequency dependent gain variation for each spectrum based on a reference spectrum.
    """
    x = np.arange(psd.shape[1])
    np.divide(psd, CubicSpline(x, psd_ref)(x,0), out=psd)
    return psd

def moving_frequency_median(psd: NDArray, window_size: int) -> NDArray:
    if window_size <= 1:
        return psd

    bins = psd.shape[1]
    psd_med = np.zeros((psd.shape[0], bins - window_size))

    for i in range(bins - window_size):
        psd_med[:,i] = np.median(psd[:,i:i+window_size], axis=1)

    return psd_med

def moving_time_median(psd: NDArray, window_size: int) -> NDArray:
    if window_size <= 1:
        return psd
    
    num_meas, bins = psd.shape
    psd_med = np.zeros((num_meas - window_size, bins))
    for i in range(num_meas - window_size):
        psd_med[i,:] = np.median(psd[i:i+window_size,:], axis=0)

    return psd_med

def zero_baseline(psd: NDArray) -> NDArray:
    bins = psd.shape[1]
    psd_avg = np.repeat(np.mean(psd, axis=1)[:, np.newaxis], bins, axis=1)
    return psd - psd_avg

def process_psd(psd: NDArray, bins_med_freq: int, bins_med_time: int, psd_ref: NDArray = None) -> NDArray:
    """
    Processes the raw power spectral density by
    1) removing the gain variation w.r.t. frequency of the receiver (*1)
    2) applying an optional moving window in which the median is taken over different measurements at a fixed frequency
    3) applying an optional moving window in which the median is taken over different frequency bins for a fixed measurement
    4) zeroing the noise floor of all measurements.

    *1 The gain variation of the receiver gain can be passed explicitly as a PSD measured with e.g. 50 Ohms connected instead of the antenna. Alternatively, the gain variation is estimated based on the average over all measurements. Note that this assumes that the hydrogenline is not stationary and experiences a significant Doppler-shift. If not, it will be averaged out.
    """
    
    if psd_ref is None:
        psd_ref = derive_reference_psd(psd)

    psd = remove_frequency_gain_variation(psd, psd_ref)
    psd = moving_time_median(psd, bins_med_time)
    psd = moving_frequency_median(psd, bins_med_freq)
    psd = zero_baseline(psd)

    return psd