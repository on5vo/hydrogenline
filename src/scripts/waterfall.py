import argparse

from hydrogenline.data import Measurement, path_waterfall

def main():
    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Waterfall", description="Generate waterfall plot from data")
    parser.add_argument("folder", help="Folder to save data")
    parser.add_argument("-b", "--bins", type=int, default=1, help="Number of bins for the moving median across frequency. Set to 1 to disable. Disabled by default.")
    parser.add_argument("-m", "--meas", type=int, default=1, help="Number of measurements for the moving median across time. Set to 1 to disable. Disabled by default.")
    parser.add_argument("-p", "--peak", type=float, default=0.1, help="Peak value on color scale with respect to the maximum value of the data. Defaults to 0.1.")

    args = parser.parse_args()
    Measurement(args.folder).save_waterfall(args.peak)

if __name__ == "__main__":
    main()