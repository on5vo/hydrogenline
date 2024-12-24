import numpy as np
from rtlsdr import RtlSdr
from typing import List, Callable
from numpy.typing import NDArray

class SDR:

    def __init__(self,
                 sample_rate: int = 2048000,
                 center_freq: int = 1420000000,
                 gain: float = 0.0,
                 bins: int = 2048
                 ) -> None:
        """
        Initialize the SDR wrapper.

        Parameters:
        ---
        - sample_rate: Sampling rate in Hz (default 2048 kHz)
        - center_freq: Center frequency in Hz (default 1.42 GHz)
        - gain: Gain setting in dB (default 0.0)
        - bins: Number of frequency bins for FFT (default 2048)
        """

        self.bins = bins
        
        # Setup RTL SDR
        self.dongle = RtlSdr()
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.dongle.set_agc_mode(False)
        self.dongle.set_bias_tee(False)
        self.dongle.set_direct_sampling(False)
        self.dongle.set_manual_gain_enabled(True)
        self.gain = gain
    
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

    def get_valid_gains(self) -> List[float]:
        """
        Returns the list of valid gain values for the RTL-SDR.
        """
        return self.dongle.valid_gains_db

    def get_samples(self) -> NDArray[np.float32]:
        """
        Get a sample from the RTL-SDR.
        
        Returns:
        ---
        - NumPy array of samples.
        """
        return self.dongle.read_samples(num_samples=self.bins)
    
    def to_psd(self, x: NDArray, window: Callable) -> NDArray[np.float64]:
        """
        Convert samples to Power Spectral Density (PSD) using FFT.
        
        Parameters:
        ---
        - x: Samples to be transformed.
        - window: Window function for smoothing.
        
        Returns:
        ---
        - PSD of the samples.
        """
        psd = np.power(np.abs(np.fft.fftshift(np.fft.fft(x*window(self.bins)))), 2)
        return psd / self.sample_rate / np.sum(np.power(window(self.bins), 2))
    
    def get_frequency(self) -> NDArray:
        return self.center_freq + np.linspace(-1,1,num=self.bins)*self.sample_rate/2
    
    def get_averaged_spectrum(self, averages: int, windows: List[Callable]) -> NDArray[np.float64]:
        """
        Get an averaged spectrum from multiple FFT samples.

        Parameters:
        ---
        - averages: The number of times to average the spectrum.
        - windows: List of window functions to apply for smoothing.

        Returns:
        ---
        - Averaged power spectral density.
        """
        num_windows = len(windows)
        S = np.zeros((num_windows, self.bins))

        for _ in range(averages):
            samples = self.get_samples()

            for i in range(num_windows):
                S[i,:] += self.to_psd(samples, windows[i])

        return S/averages
