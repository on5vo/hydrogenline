import sys
import numpy as np
import json
import argparse
from rtlsdr.rtlsdr import LibUSBError

from hydrogenline.sdr import SDR
from hydrogenline.io import get_reference_folder, get_reference_path
from hydrogenline.utils import Bar, format_timedelta

def convert_windows_to_functions(windows):
    window_functions = {
        "hamming": np.hamming,
        "hanning": np.hanning,
        "blackman": np.blackman,
        "bartlett": np.bartlett
    }

    return [window_functions[window] for window in windows]

def main():
    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Reference")
    parser.add_argument("fname", help="File name to save data to")
    parser.add_argument("-s", "--sample-rate", type=int, help="Sample rate in ksps", default=2048)
    parser.add_argument("-b", "--bins", type=int, help="Number of bins or, equivalently, number of samples", default=2048)
    parser.add_argument("-w", "--windows", type=str, help="Window functions", nargs="*", choices=["hamming", "hanning", "blackman", "bartlett"], default=["hanning"])
    parser.add_argument("-g", "--gain", type=int, help="Gain in dB", default=0)
    parser.add_argument("-a", "--averages", type=int, help="Number of averages", default=100000)

    args = parser.parse_args()
    
    try:
        sdr = SDR(gain=args.gain, bins=args.bins, sample_rate=int(args.sample_rate*1e3))
    except LibUSBError:
        print("No SDR device found. Exiting.")
        sys.exit(1)

    # Get actual SDR gain and center frequency
    args.gain = sdr.gain
    vars(args)["center_freq"] = sdr.center_freq

    # Save settings to a file
    with open(get_reference_folder() / f"{args.fname}.json", "wb") as f:
        f.write(json.dumps(vars(args)).encode())

    window_functions = convert_windows_to_functions(args.windows)

    progressbar = Bar(args.averages)

    progressbar.prefix = f"Capturing data"
    progressbar.reset()

    S = sdr.get_averaged_spectrum(args.averages, window_functions, progressbar=progressbar)
    np.save(get_reference_path(f"{args.fname}.npy"), S)

    progressbar.finish()

    print("Done!", flush=True)

if __name__ == "__main__":
    main()