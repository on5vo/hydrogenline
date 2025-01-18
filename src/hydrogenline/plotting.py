import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from hydrogenline.io import load_settings, get_data_path, parse_datetime
from datetime import datetime

from typing import Tuple, List
from numpy.typing import NDArray

plt.rcParams.update({
    'figure.constrained_layout.use': True,
    'font.size': 12,
    'axes.edgecolor': 'gray',
    'xtick.color':    'gray',
    'ytick.color':    'gray',
    'axes.labelcolor':'gray',
    'axes.spines.right':False,
    'axes.spines.top':  False,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.size': 6,
    'xtick.minor.size': 4,
    'ytick.major.size': 6,
    'ytick.minor.size': 4,
    'xtick.major.pad': 15,
    'xtick.minor.pad': 15,
    'ytick.major.pad': 15,
    'ytick.minor.pad': 15,
    })

def _get_hours(folder: str) -> Tuple[List[int], List[int]]:
    """
    Calculates the y-axis labels for the waterfall plot based on the datetimes
    extracted from files in the given folder. Returns the indices and adjusted
    hour values for plotting.

    Args:
        folder (str): The folder containing the data files.

    Returns:
        Tuple[List[int], List[int]]: Indices of the unique hours and the corresponding
        hour values (adjusted for time of day).
    """
    path = get_data_path(folder)
    datetimes = np.asarray(sorted([parse_datetime(file) for file in path.iterdir()]))

    # Add 24h per measured day to keep it after np.unique
    day_offset = np.asarray([(dt.day - datetimes[0].day)*24 for dt in datetimes])
    hours = np.asarray([dt.hour + offset for dt, offset in zip(datetimes, day_offset)])
    _, hour_inds = np.unique(hours, return_index=True)

    # Remove 24h per measured day to show time of day
    hours = hours[hour_inds] - day_offset[hour_inds]

    # Only show first hour if it is close to the exact hour
    MINUTE_THRESHOLD = 5
    if MINUTE_THRESHOLD < datetimes[hour_inds[0]].minute or datetimes[hour_inds[0]].minute < (60 - MINUTE_THRESHOLD):
        hours = hours[1:]
        hour_inds = hour_inds[1:]

    return hour_inds, hours

def _get_frequency_range(folder: str, bins: int) -> NDArray:
    """
    Calculates the frequency range of the Power Spectral Density (PSD) in MHz 
    based on the sample rate and center frequency defined in the settings for 
    the specified folder. The bins are required as a parameter as some dsp
    functions can crop the number of bins compared to the value defined in
    the settings.

    Args:
        folder (str): The folder containing the data files used for calculation.
        bins (int): The number of frequency bins in the PSD.

    Returns:
        NDArray: An array of frequency values (in MHz) corresponding to the 
                 given number of bins, centered around the center frequency 
                 and spanning the sample rate range.
    """
    settings = load_settings(folder)
    sample_rate = settings["sample_rate"]/1e3
    center_freq = settings["center_freq"]/1e6
    return np.linspace(-sample_rate/2, sample_rate/2, bins) + center_freq

def waterfall(psd: NDArray, peak: float, folder: str, cmap: str = "gray") -> Tuple[matplotlib.figure.Figure, plt.Axes]:
    """
    Creates a waterfall plot of the Power Spectral Density (PSD) data over time 
    and frequency. This function plots the PSD with appropriate scaling and 
    labels the x-axis with frequency values (in MHz) and the y-axis with time 
    labels (in hours).

    Args:
        psd (NDArray): A 2D array representing the Power Spectral Density (PSD)
                       values. The shape should be (time, frequency bins).
        peak (float): The peak scaling factor for the color scale (used for normalization).
        folder (str): The folder containing the data files, used to calculate the
                      time and frequency ranges for the plot.
        cmap (str, optional): The colormap to use for the plot. Default is "gray".

    Returns:
        Tuple[matplotlib.figure.Figure, plt.Axes]:
            - A `matplotlib.figure.Figure` object representing the created figure.
            - A `matplotlib.Axes` object representing the axes of the plot.
    """
    _, bins = psd.shape

    # Determine time stamps of measurements
    hour_inds, hours = _get_hours(folder)

    # Determine frequency range
    f_MHz = _get_frequency_range(folder, bins)

    fig, ax = plt.subplots(figsize=(8,6))
    fig.set_facecolor("black")

    ax.imshow(psd, vmin=0, vmax=peak*np.max(psd), cmap=cmap, aspect="auto")
    ax.set_xticks([0, bins//2, bins], labels=[f"{f_MHz[0]:.0f}", f"{f_MHz[bins//2]:.0f} MHz", f"{f_MHz[-1]:.0f}"])
    ax.set_yticks(hour_inds, labels=[f"{int(h)}h" for h in hours])
    ax.spines[['bottom', 'left']].set_position(('outward', 20))

    return fig, ax

def psd(psd: NDArray, folder: str, min: float, max: float, datetime: datetime) -> Tuple[matplotlib.figure.Figure, plt.Axes]:
    bins = len(psd)
    # Determine frequency range
    f_MHz = _get_frequency_range(folder, bins)

    fig, ax = plt.subplots(figsize=(8,6))

    ax.set_title(datetime.strftime('%Y/%m/%d %H:%M:%S'), color="gray")

    ax.plot(f_MHz, psd, color='k')

    ax.set_xticks([f_MHz[0], f_MHz[bins//2], f_MHz[-1]], labels=[f"{f_MHz[0]:.0f}", f"{f_MHz[bins//2]:.0f} MHz", f"{f_MHz[-1]:.0f}"])
    ax.spines[['bottom', 'left']].set_position(('outward', 20))

    ax.set_ylim((min, max))
    ax.set_yticks([])
    ax.set_xlim((f_MHz[0], f_MHz[-1]))
    ax.spines['left'].set_visible(False)

    return fig, ax