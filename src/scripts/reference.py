import sys
import numpy as np
import json
import argparse
from rtlsdr.rtlsdr import LibUSBError

from hydrogenline.sdr import SDR
from hydrogenline.data import path_reference_settings, path_reference_data
from hydrogenline.utils import Bar, convert_windows_to_functions

def main():
    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Reference")
    parser.add_argument("fname", help="File name to save data to")
    parser.add_argument("-s", "--sample-rate", type=int, help="Sample rate in ksps. Defaults to 2048 ksps.", default=2048)
    parser.add_argument("-b", "--bins", type=int, help="Number of bins or, equivalently, number of samples passed as the exponent of 2. Defaults to 16, or 2^16 = 65536.", default=16)
    parser.add_argument("-w", "--windows", type=str, help="Window functions. Defaults to all available options: hanning, hamming, blackman, bartlett.", nargs="*", choices=["hamming", "hanning", "blackman", "bartlett"], default=["hanning", "hamming", "blackman", "bartlett"])
    parser.add_argument("-g", "--gain", type=int, help="Gain in dB. Defaults to zero.", default=0)
    parser.add_argument("-t", "--tint", type=int, help="Time in seconds to average over. Defaults to 120 seconds.", default=120)

    args = parser.parse_args()

    # Convert bins exponent to actual number of bins
    vars(args)["bins"] = 2**args.bins

    # Convert sample rate to sps
    vars(args)["sample_rate"] = int(args.sample_rate*1e3)

    # Time per measurement in seconds
    time_per_meas = args.bins/(args.sample_rate)
    # Number of averages rounded to an int
    vars(args)["averages"] = args.tint//time_per_meas
    # Set actual time, accounting for the rounding
    vars(args)["tint"] = args.averages*time_per_meas
    
    try:
        sdr = SDR(gain=args.gain, bins=args.bins, sample_rate=args.sample_rate)
    except LibUSBError:
        print("No SDR device found. Exiting.")
        sys.exit(1)

    # Get actual SDR gain and center frequency
    args.gain = sdr.gain
    vars(args)["center_freq"] = sdr.center_freq

    # Save settings to a file
    with open(path_reference_settings(args.fname), "wb") as f:
        f.write(json.dumps(vars(args)).encode())

    window_functions = convert_windows_to_functions(args.windows)

    progressbar = Bar(args.averages)

    progressbar.prefix = f"Capturing data"
    progressbar.reset()

    S = sdr.get_averaged_spectrum(args.averages, window_functions, progressbar=progressbar)
    np.save(path_reference_data(args.fname), S)

    progressbar.finish()

    print("Done!", flush=True)

if __name__ == "__main__":
    main()