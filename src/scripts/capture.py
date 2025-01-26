import sys
import numpy as np
from datetime import datetime
from tzlocal import get_localzone
import time
import json
import argparse
from rtlsdr.rtlsdr import LibUSBError

from hydrogenline.sdr import SDR
from hydrogenline.data import path_root, path_data
from hydrogenline.utils import Bar, format_timedelta, convert_windows_to_functions

def main():
    local_tz = get_localzone()

    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Capture")
    parser.add_argument("folder", help="Folder to save data")
    parser.add_argument("-s", "--sample-rate", type=int, help="Sample rate in ksps. Defaults to 2048 ksps.", default=2048)
    parser.add_argument("-b", "--bins", type=int, help="Number of bins or, equivalently, number of samples passed as the exponent of 2. Defaults to 16, or 2^16 = 65536.", default=16)
    parser.add_argument("-w", "--windows", type=str, help="Window functions. Defaults to Hanning.", nargs="*", choices=["hamming", "hanning", "blackman", "bartlett"], default=["hanning"])
    parser.add_argument("-g", "--gain", type=int, help="Gain in dB. Defaults to zero.", default=0)
    parser.add_argument("-t", "--tint", type=int, help="Time in seconds to average over. Defaults to 120 seconds.", default=120)
    parser.add_argument("-r", "--reference", type=str, help="Name of reference measurement file", default=None)
    parser.add_argument("--start", type=str, help="Start date and time in the format YYYYMMDD HH:MM", default=datetime.now(local_tz).strftime("%Y%m%d %H:%M"))
    parser.add_argument("--stop", type=str, help="End date and time in the format YYYYMMDD HH:MM", default=None)

    args = parser.parse_args()

    # Convert bins exponent to actual number of bins
    vars(args)["bins"] = 2**args.bins

    # Convert sample rate to sps
    vars(args)["sample_rate"] = int(args.sample_rate*1e3)

    # Time per measurement in seconds
    time_per_meas = args.bins/(args.sample_rate)
    # Number of averages rounded to an int
    vars(args)["averages"] = int(args.tint//time_per_meas)
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
    with open(path_root(args.folder) / f"settings.json", "wb") as f:
        f.write(json.dumps(vars(args)).encode())

    window_functions = convert_windows_to_functions(args.windows)

    # Schedule measurements
    t_start = datetime.strptime(args.start, "%Y%m%d %H:%M").replace(tzinfo=local_tz)
    t_stop = datetime.strptime(args.stop, "%Y%m%d %H:%M").replace(tzinfo=local_tz) if args.stop is not None else None

    t_now = datetime.now(local_tz)
    while t_now < t_start:
        t_now = datetime.now(local_tz)
        print(f"Waiting to start in {format_timedelta(t_start - t_now)}", end="\r", flush=True)
        time.sleep(1)

    progressbar = Bar(args.averages)

    # Start capturing data
    while t_stop is None or t_stop > datetime.now(local_tz):
        t_now = datetime.now(local_tz)

        progressbar.prefix = f"Capturing data {t_now.strftime('%Y%m%d %H:%M')}"
        progressbar.reset()

        S = sdr.get_averaged_spectrum(args.averages, window_functions, progressbar=progressbar)
        np.save(path_data(args.folder) / f"{t_now.strftime('%Y%m%d_%H_%M_%S')}.npy", S)

    progressbar.finish()

    print("Done!", flush=True)

if __name__ == "__main__":
    main()