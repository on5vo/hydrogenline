import numpy as np
from pathlib import Path
import matplotlib
from matplotlib import pyplot as plt
import json
from datetime import datetime

from hydrogenline.utils import Bar

from typing import List, Dict
from numpy.typing import NDArray


def create_path(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def path_root(name: str) -> Path:
    return create_path(Path.home() / ".hydrogenline" / name)

def path_data(name: str) -> Path:
    return create_path(path_root(name) / "data")

def path_settings(name: str) -> Path:
    return path_root(name) / "settings.json"

def path_reference() -> Path:
    return create_path(path_root("references"))

def path_reference_data(name: str) -> Path:
    return path_reference() / f"{name}.npy"

def path_reference_settings(name: str) -> Path:
    return path_reference() / f"{name}.json"

def path_waterfall(name: str, window: str, format: str = "webp") -> Path:
    path = create_path(path_root(name) / "waterfall")
    return path / f"{window}.{format}"

def path_spectra(name: str, window: str, datetime: datetime, format: str = "webp") -> Path:
    path = create_path(path_root(name) / "spectra" / window)
    return path / f"{datetime.strftime('%Y%m%d_%H_%M_%S')}.{format}"


def W2dBm(p):
    return 10*np.log10(p*1e3)

def dBm2W(p):
    return np.power(10, p/10 - 3)


class Measurement:

    def __init__(self, name: str) -> None:
        # Settings
        self.folder: str = ""
        self.bins: int = 0
        self.sample_rate: int = 0
        self.windows: List[str] = []
        self.gain: int = 0
        self.averages: int = 0
        self.reference: str = ""
        self.start: str = ""
        self.stop: str = ""
        self.center_freq: int = 0

        self.psd: Dict[str, NDArray[np.float64]] = {}
        self.dates: List[datetime] = []

        # Load settings and measurement data
        self._load_settings(name)
        self._load_data(name)

    def _load_settings(self, name: str) -> None:
        # Load settings from file
        with open(path_settings(name), "rb") as f:
            settings = json.loads(f.read())

        # Create class parameters from settings
        for k, v in settings.items():
            setattr(self, k, v)

        # Load reference measurement if specified
        if self.reference is not None:
            self.reference_psd = np.load(path_reference_data(self.reference), allow_pickle=True).item()

            with open(path_reference_settings(self.reference), "rb") as f:
                reference_settings = json.loads(f.read())

            # Check if reference file is compatible with measurements
            if not reference_settings["bins"] == self.bins:
                print("ERROR: Reference measurement and measurement data have a different number of frequency bins.")
                exit(1)

            if not reference_settings["sample_rate"] == self.sample_rate:
                print("ERROR: Reference measurement and measurement data have a different sample rate.")
                exit(1)

            if not reference_settings["center_freq"] == self.center_freq:
                print("ERROR: Reference measurement and measurement data have a different center frequency.")
                exit(1)

            if not reference_settings["gain"] == self.gain:
                print("WARNING: Reference measurement and measurement data have different RTL-SDR gain settings.")
        else:
            print("ERROR: Non reference measurement specified.")
            exit(1)
        
    def _load_data(self, name: str) -> None:
        # Collection of all available data files
        files = [file for file in path_data(name).iterdir() if file.is_file()]

        self.num_meas = len(files)

        # Init dictionary
        self.psd = {}
        for window in self.windows:
            self.psd[window] = np.zeros((self.num_meas, self.bins))

        # Load data from stored files into dict grouped per window function
        for n, file in enumerate(files):
            loaded_psd = np.load(file, allow_pickle=True).item()

            for window in self.windows:
                self.psd[window][n,:] = loaded_psd[window]

        # Gather time stamps of data
        self.dates = [datetime.strptime(file.name.removesuffix(".npy"), "%Y%m%d_%H_%M_%S") for file in files]

    @property
    def psd_dBm(self) -> Dict[str, NDArray[np.float64]]:
        return dict((k, W2dBm(v)) for k, v in self.psd.items())
    
    @psd_dBm.setter
    def psd_dBm(self, p: Dict[str, NDArray[np.float64]]) -> None:
        self.psd = dict((k, dBm2W(v)) for k, v in p.items())

    @property
    def reference_psd_dBm(self) -> Dict[str, NDArray[np.float64]]:
        return dict((k, W2dBm(v)) for k, v in self.reference_psd.items())
    
    @property
    def frequencies(self) -> NDArray[np.float64]:
        return np.linspace(-0.5, 0.5, num=self.bins)*self.sample_rate*1e3 + self.center_freq

    def process(self, normalize: bool = True) -> Dict[str, NDArray[np.float64]]:
        # Remove frequency gain variation
        # Reference psd is normalized to its average power of the measured band to minimize influence on the absolute power of the measurement
        psds = dict((window, psd/self.reference_psd[window]*np.mean(self.reference_psd[window])) for window, psd in self.psd.items())

        if normalize:
            psds_avg = dict((window, np.repeat(np.mean(psd, axis=1)[:, np.newaxis], self.bins, axis=1)) for window, psd in psds.items())

            psds = dict((window, psd - psd_avg) for window, psd, psd_avg in zip(self.windows, psds.values(), psds_avg.values()))

        return psds
    
    def save_waterfall(self, peak: float) -> None:
        f_MHz = self.frequencies/1e6

        # Get y-axis labels from measurement timestamps
        # Add 24h per measured day to keep it after np.unique
        day_offset = np.asarray([(dt.day - self.dates[0].day)*24 for dt in self.dates])
        hours = np.asarray([dt.hour + offset for dt, offset in zip(self.dates, day_offset)])
        _, hour_inds = np.unique(hours, return_index=True)

        # Remove 24h per measured day to show time of day
        hours = hours[hour_inds] - day_offset[hour_inds]

        # Only show first hour if it is close to the exact hour
        MINUTE_THRESHOLD = 5
        if MINUTE_THRESHOLD < self.dates[hour_inds[0]].minute or self.dates[hour_inds[0]].minute < (60 - MINUTE_THRESHOLD):
            hours = hours[1:]
            hour_inds = hour_inds[1:]

        # Create waterfall plot for each window function
        for window, psds in self.process().items():
            fig, ax = plt.subplots(figsize=(6,len(hours)*0.3))
            fig.set_facecolor("black")
            ax.set_title(f"{self.dates[0].strftime('%Y/%m/%d %H:%M')} - {self.dates[-1].strftime('%Y/%m/%d %H:%M')}", color="gray")

            ax.imshow(psds, vmin=0, vmax=peak*np.max(psds), cmap="gray", aspect="auto")

            ax.set_xticks([0, self.bins//2, self.bins], labels=[f"{f_MHz[0]:.0f}", f"{f_MHz[self.bins//2]:.0f} MHz", f"{f_MHz[-1]:.0f}"])
            ax.set_yticks(hour_inds, labels=[f"{int(h)}h" for h in hours])

            ax.spines[['bottom', 'left']].set_position(('outward', 20))

            fig.savefig(path_waterfall(self.folder, window))
    
    def save_spectra(self, format: str = "webp") -> None:
        f_MHz = self.frequencies/1e6

        progressbar = Bar(len(self.windows)*self.num_meas, prefix="Creating PSD plots")

        for window, psds in self.process(normalize=False).items():

            mean = np.mean(psds)
            mean_dBm = W2dBm(mean)

            for i, psd in enumerate(psds):
                psd = W2dBm(psd)

                fig, ax = plt.subplots()
                ax.set_title(self.dates[i].strftime('%Y/%m/%d %H:%M:%S'), color="gray")
                ax.plot(f_MHz, psd, color='k')

                ax.set_xticks([f_MHz[0], f_MHz[self.bins//2], f_MHz[-1]], labels=[f"{f_MHz[0]:.0f}", f"{f_MHz[self.bins//2]:.0f} MHz", f"{f_MHz[-1]:.0f}"])
                ax.spines[['bottom', 'left']].set_position(('outward', 20))

                ymax = np.ceil(np.max(psd))
                ymin = np.floor(mean_dBm - 1)

                ax.set_ylim((ymin, ymax))
                ax.set_xlim((f_MHz[0], f_MHz[-1]))
                ax.set_ylabel("Power (dBm)", ha="left", y=1.03, rotation=0, labelpad=0)

                fig.savefig(path_spectra(self.folder, window, self.dates[i], format=format))

                plt.close(fig)

                progressbar.update()

        progressbar.finish()