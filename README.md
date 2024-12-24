# Hydrogenline

This package provides scripts to interface with the RTL-SDR to automate measurements for [measuring the hydrogen line](https://www.on5vo.be/html/radio/hydrogenline.html).

Data is automatically stored in your home directory under `~/.hydrogenline`. It consists of a settings file `settings.json` and the averaged spectra under `[folder]/data/YYYMMDD_HH:MM:SS.npy`.

# Installation

The python package can be installed as follows from the CLI:

1) Clone the project and cd into it.
2) Create a virtual environment and activate it.
3) Install `setuptools`.
4) Install this package through `pip install .`.

To use the RTL-SDR on Linux, it must first be blacklisted as a device.

# Scripts

The scripts available as CLI executables:

- `capture`: captures samples repeatedly from the RTL-SDR, calculates and averages the PSD, and stores them