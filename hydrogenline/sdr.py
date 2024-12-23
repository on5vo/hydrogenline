import numpy as np

from rtlsdr import RtlSdr

from typing import List
from numpy.typing import NDArray

class SDR:

    def __init__(self,
                 sample_rate: int = 2048000000,
                 center_freq: int = 1420000000,
                 gain: float = 0.0,
                 bins: int = 2048
                 ) -> None:
        
        # Init properties
        self._sample_rate = None
        self._center_freq = None
        self._gain = None

        self.bins = bins
        
        # Setup RTL SDR
        self.dongle = RtlSdr()
        self.sample_rate = sample_rate
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.dongle.set_agc_mode(False)
        self.dongle.set_bias_tee(False)
        self.dongle.set_direct_sampling(False)
        self.dongle.set_manual_gain_enabled(True)
        self.gain = gain

    def get_valid_gains(self) -> List:
        return self.dongle.valid_gains_db
    
    @property
    def gain(self) -> float:
        return self._gain

    @gain.setter
    def gain(self, gain: float) -> None:
        self.dongle.gain = gain
        self._gain = self.dongle.gain

    @property
    def sample_rate(self) -> int:
        return self._sample_rate
    
    @sample_rate.setter
    def sample_rate(self, sample_rate: int) -> None:
        self.dongle.sample_rate = sample_rate
        self._sample_rate = self.dongle.sample_rate

    @property
    def center_freq(self) -> int:
        return self._center_freq
    
    @center_freq.setter
    def center_freq(self, center_freq: int) -> None:
        self.dongle.center_freq = center_freq
        self._center_freq = self.dongle.center_freq

    def get_samples(self) -> NDArray:
        return self.dongle.read_samples(num_samples=self.bins)
    
    def to_psd(self, x: NDArray, window: function) -> NDArray:
        PSDw = np.sum(np.power(window(self.bins), 2))
        return np.power(np.abs(np.fft.fftshift(np.fft.fft(x*window(self.bins)))), 2)/self.sample_rate/PSDw
    
    def get_frequency(self) -> NDArray:
        return self.center_freq + np.linspace(-1,1,num=self.bins)*self.sample_rate/2
    
    def get_averaged_spectrum(self, averages: int, windows: List[function]) -> NDArray:
        num_windows = len(windows)
        S = np.zeros((num_windows, self.bins))

        for _ in range(averages):
            samples = self.get_samples()

            for i in range(num_windows):
                S[i,:] += self.to_psd(samples, windows[i])

        return S/averages
