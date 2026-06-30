"""
Plot national annual total electricity demand (TWh/yr) vs ReEDS model year,
one line per EER2025 demand scenario, from the Zenodo .h5 demand profiles.

Data: https://zenodo.org/records/18435264
Each state dataset = 131400 hourly values = 15 weather years x 8760 hours, in MWh/h.
We sum hours -> annual MWh per weather year, sum states -> national, /1e6 -> TWh.
The line is the mean over the 15 weather years; the band is the min-max spread.

Run with user site-packages disabled to avoid the NumPy 2.x conflict:
    PYTHONNOUSERSITE=1 python plot_annual_demand.py
"""
import os
import h5py
import numpy as np
import matplotlib.pyplot as plt

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HOURS_PER_YEAR = 8760
N_WEATHER_YEARS = 15

# filename -> nice label for the legend
SCENARIOS = {
    "demand_EER2025_Baseline_AEO2023.h5": "Baseline (AEO2023)",
    "demand_EER2025_IRAlow.h5":           "IRA low",
    "demand_EER2025_100by2050.h5":        "100% by 2050",
}


def national_annual_twh(path):
    """Return (model_years, mean_twh, min_twh, max_twh) arrays."""
    model_years, means, mins, maxs = [], [], [], []
    with h5py.File(path, "r") as h:
        years = sorted(int(k) for k in h.keys())
        for yr in years:
            g = h[str(yr)]
            states = [k for k in g.keys() if k not in ("datetime", "columns")]
            # national annual total per weather year, in MWh
            nat = np.zeros(N_WEATHER_YEARS, dtype=np.float64)
            for s in states:
                arr = g[s][()].astype(np.float64)            # (131400,)
                arr = arr.reshape(N_WEATHER_YEARS, HOURS_PER_YEAR)
                nat += arr.sum(axis=1)                        # sum hours -> annual MWh
            nat_twh = nat / 1e6                              # MWh -> TWh
            model_years.append(yr)
            means.append(nat_twh.mean())
            mins.append(nat_twh.min())
            maxs.append(nat_twh.max())
    return (np.array(model_years), np.array(means),
            np.array(mins), np.array(maxs))


def main():
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, 10))

    for i, (fname, label) in enumerate(SCENARIOS.items()):
        path = os.path.join(DATA_DIR, fname)
        yrs, mean, lo, hi = national_annual_twh(path)
        c = colors[i]
        ax.fill_between(yrs, lo, hi, color=c, alpha=0.15)
        ax.plot(yrs, mean, "-o", color=c, lw=2, label=label)
        print(f"{label:20s} " + "  ".join(f"{y}:{m:6.0f}" for y, m in zip(yrs, mean)))

    ax.set_xlabel("ReEDS model year")
    ax.set_ylabel("National annual electricity demand (TWh/yr)")
    ax.set_title("Gross end-use electricity demand, contiguous US\n"
                 "EER2025 scenarios (line = mean of 15 weather years, band = min–max)")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Scenario")
    fig.tight_layout()

    out = os.path.join(os.path.dirname(__file__), "national_annual_demand.png")
    fig.savefig(out, dpi=150)
    print("\nSaved:", out)


if __name__ == "__main__":
    main()
