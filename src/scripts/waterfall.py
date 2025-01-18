import argparse
from hydrogenline.io import load_data, load_settings, get_waterfall_path, load_reference
from hydrogenline.dsp import process_psd
from hydrogenline.plotting import waterfall
from hydrogenline.utils import Bar

def main():
    # Load settings from CLI
    parser = argparse.ArgumentParser(prog="Waterfall", description="Generate waterfall plot from data")
    parser.add_argument("folder", help="Folder to save data")
    parser.add_argument("-b", "--bins", type=int, default=1, help="Number of bins for the moving median across frequency. Set to 1 to disable. Disabled by default.")
    parser.add_argument("-m", "--meas", type=int, default=1, help="Number of measurements for the moving median across time. Set to 1 to disable. Disabled by default.")
    parser.add_argument("-p", "--peak", type=float, default=0.1, help="Peak value on color scale with respect to the maximum value of the data. Defaults to 0.1.")

    args = parser.parse_args()

    # Load settings to get number of windows and reference measurement file name
    settings = load_settings(args.folder)
    num_windows = len(settings["windows"])

    # Load measured PSDs
    _, psds = load_data(args.folder)

    # Load reference measurement, if it exists
    reference_path = settings.get("reference", None)
    if reference_path is not None:
        psds_ref = load_reference(reference_path)
    else:
        psds_ref = None

    path = get_waterfall_path(args.folder)

    progressbar = Bar(num_windows, prefix="Generating waterfall plots")
    progressbar.reset()

    for window in settings["windows"]:
        if psds_ref is not None:
            psd_ref = psds_ref[window]
        else:
            psd_ref = None

        psd = process_psd(psds[window], args.bins, args.meas, psd_ref=psd_ref)
        fig, _ = waterfall(psd, args.peak, args.folder)
        fig.savefig(path / f"{window}.jpg", bbox_inches="tight", dpi=600)
        progressbar.update()

    progressbar.finish()

if __name__ == "__main__":
    main()