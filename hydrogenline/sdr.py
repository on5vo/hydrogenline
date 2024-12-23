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
        # Setup RTL SDR
        self.dongle = RtlSdr()
        self.dongle.sample_rate = sample_rate
        self.dongle.center_freq = center_freq
        self.dongle.set_agc_mode(False)
        self.dongle.set_bias_tee(False)
        self.dongle.set_direct_sampling(False)
        self.dongle.set_manual_gain_enabled(True)
        self.dongle.gain = gain

        self.bins = bins

    def get_valid_gains(self) -> List:
        return self.dongle.valid_gains_db
    
    def get_gain(self) -> float:
        return self.dongle.gain

    def set_gain(self, gain: float) -> None:
        self.dongle.gain = gain

    def get_samples(self) -> NDArray:
        return self.dongle.read_samples(num_samples=self.bins)
    
    def to_spectrum(self, x: NDArray, window: function) -> NDArray:
        return np.power(np.abs(np.fft.fftshift(np.fft.fft(x*window(self.bins)))), 2)
    
    def get_spectrum(self, window: function) -> NDArray:
        return np.power(np.abs(np.fft.fftshift(np.fft.fft(self.get_samples()*window(self.bins)))), 2)
    
    def get_frequency(self) -> NDArray:
        return self.dongle.center_freq + np.linspace(-1,1,num=self.bins)*self.dongle.sample_rate/2
    
    def get_averaged_spectrum(self, averages: int, windows: List[function]) -> NDArray:
        num_windows = len(windows)
        S = np.zeros((num_windows, self.bins))

        for _ in range(averages):
            samples = self.get_samples()

            for i in range(num_windows):
                S[i,:] += self.to_spectrum(samples, windows[i])

        return S/averages
