import argparse
from hydrogenline.io import load_data, load_settings, get_waterfall_path
from hydrogenline.dsp import process_psd
from hydrogenline.plotting import waterfall
from hydrogenline.utils import Bar

def main():
    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Waterfall", description="Generate waterfall plot from data")
    parser.add_argument("folder", help="Folder to save data")
    parser.add_argument("-b", "--bins", type=int, default=1, help="Number of bins for the moving median across frequency. Set to 1 to disable. Disabled by default")
    parser.add_argument("-m", "--meas", type=int, default=1, help="Number of measurements for the moving median across time. Set to 1 to disable. Disabled by default")
    parser.add_argument("-p", "--peak", type=float, default=0.1, help="Peak value on color scale with respect to the maximum value of the data")

    args = parser.parse_args()

    settings = load_settings(args.folder)
    _, psds = load_data(args.folder)

    num_windows = len(settings["windows"])
    path = get_waterfall_path(args.folder)

    progressbar = Bar(num_windows, prefix="Generating waterfall plots")
    progressbar.reset()

    for i in range(num_windows):
        psd = process_psd(psds[i], args.bins, args.meas)
        fig, _ = waterfall(psd, args.peak, args.folder)
        fig.savefig(path / f"{settings['windows'][i]}.jpg", bbox_inches="tight", dpi=600)
        progressbar.update()

    progressbar.finish()

if __name__ == "__main__":
    main()