import sys
import numpy as np
from datetime import datetime
from tzlocal import get_localzone
import time
import json
import argparse
from rtlsdr.rtlsdr import LibUSBError

from hydrogenline.sdr import SDR
from hydrogenline.io import get_path, get_data_path

def convert_windows_to_functions(windows):
    window_functions = {
        "hamming": np.hamming,
        "hanning": np.hanning,
        "blackman": np.blackman,
        "bartlett": np.bartlett
    }

    return [window_functions[window] for window in windows]

def main():
    local_tz = get_localzone()

    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Capture")
    parser.add_argument("folder", help="Folder to save data")
    parser.add_argument("-s", "--sample-rate", type=int, help="Sample rate in ksps", default=2048)
    parser.add_argument("-b", "--bins", type=int, help="Number of bins or, equivalently, number of samples", default=2048)
    parser.add_argument("-w", "--windows", type=str, help="Window functions", nargs="*", choices=["hamming", "hanning", "blackman", "bartlett"], default=["hanning"])
    parser.add_argument("-g", "--gain", type=int, help="Gain in dB", default=0)
    parser.add_argument("-a", "--averages", type=int, help="Number of averages", default=100000)
    parser.add_argument("--start", type=str, help="Start date and time in the format YYYYMMDD HH:MM", default=datetime.now(local_tz).strftime("%Y%m%d %H:%M"))
    parser.add_argument("--stop", type=str, help="End date and time in the format YYYYMMDD HH:MM", default=None)

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
    with open(get_path(args.folder) / f"settings.json", "wb") as f:
        f.write(json.dumps(vars(args)).encode())

    window_functions = convert_windows_to_functions(args.windows)

    # Schedule measurements
    t_start = datetime.strptime(args.start, "%Y%m%d %H:%M")
    t_stop = datetime.strptime(args.stop, "%Y%m%d %H:%M") if args.stop is not None else None

    t_now = datetime.now(local_tz)
    wheel = ["|", "/", "-", "\\"]
    i = 0
    while t_now < t_start:
        print(f"Waiting for start time... {wheel[i%len(wheel)]}", end="\r", flush=True)
        time.sleep(1)
        i += 1

    # Start capturing data
    while t_stop is None or t_stop > t_now:
        t_now = datetime.now(local_tz)
        print(f"Capturing data... {t_now.strftime('%Y%m%d %H:%M')}", end="\r", flush=True)
        S = sdr.get_averaged_spectrum(args.averages, window_functions)
        np.save(get_data_path(args.folder) / f"{t_now.strftime('%Y%m%d_%H:%M:%S')}.npy", S)

    print("Done!", flush=True)

if __name__ == "__main__":
    main()