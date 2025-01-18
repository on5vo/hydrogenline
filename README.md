# Hydrogenline

This package provides scripts to interface with the RTL-SDR to automate measurements for [measuring the hydrogen line](https://www.on5vo.be/html/radio/hydrogenline.html).

Data and plots are automatically stored in your home directory under `~/.hydrogenline`. It consists of a settings file `settings.json` and the averaged spectra under `[folder]/data/YYYMMDD_HH_MM_SS.npy`.

# Installation

There are multiple ways of using this package. The methods below limits the scope of the scripts to the virtual environment.

## PyPi

The package is available on [PyPi](https://pypi.org/project/hydrogenline/).

Open a terminal and create a directory
```bash
mkdir hydrogenline
```
`cd` into the directory an create a virtual environment
```bash
cd hydrogenline
python -m venv .venv
```
Activate the virtual environment on Linux
```bash
source .venv/bin/activate
```
or in Window Bash
```bash
.venv\Scripts\activate.bat
```
and install the package
```bash
pip install hydrogenline
```

## GitHub

The package can also be installed from the GitHub repository.

> [!CAUTION]
> The GitHub repository contains experimental code and is used for development. Use PyPi for the most reliable version or use a tagged commit which corresponds to a PyPi version.

Open a terminal and clone the repository from github
```bash
git clone https://github.com/on5vo/hydrogenline.git
```
`cd` into the repository directory an create a virtual environment
```bash
cd hydrogenline
python -m venv .venv
```
Activate the virtual environment on Linux
```bash
source .venv/bin/activate
```
or in Window Bash
```bash
.venv\Scripts\activate.bat
```
and install the package
```bash
pip install -e .
```

## RTL-SDR

If you get the following error message, you will have to blacklist the RTL-SDR kernel modules from being directly loaded. [This](https://github.com/sdr-enthusiasts/gitbook-adsb-guide/blob/main/setting-up-rtl-sdrs/blacklist-kernel-modules.md) is a nice source explaining the process.
```
usb_claim_interface error -6
rtlsdr: error opening the RTLSDR device: Device or resource busy
```

# Use

There are several scripts available as CLI executables. In order to use them, you will have to activate the virtual environment, if you used the installation method above. These scripts include a manual which can be accessed by passing the `-h`argument (e.g. `capture -h`).

The scripts available as CLI executables:

- `reference`: capture a reference measurement of the receiver.
- `capture`: captures samples repeatedly from the RTL-SDR, calculates and averages the PSD, and stores them.
- `waterfall`: creates a waterfall plot of the measured PSDs.
- `spectra`: create PSD plots of all measurements.

For example, you want to measure the hydrogen line overnight. First, take a reference measurement with 50 Ohm connected instead of the antenna.
```bash
reference lna1-filter1-amp1 -g 50 -w hanning blackman
```
Next, after connecting the antenna back to the input of the receiver, start the measurements.
```bash
capture 20250103 -g 50 -r lna1-filter1-amp1 --start "20250103 19:00" --stop "20250104 8:00"
```
As each measurement is directly saved, you can already plot a waterfall or the spectra during the measurement campaign, if your impatience gets the better of you. Play with the `-b`, `-m` and `-p` settings if you get interference which is static in frequency (a barcode pattern). `-p`can also be tuned to reveal fainter parts of the hydrogen line spectrum.
```bash
waterfall 20250103
```