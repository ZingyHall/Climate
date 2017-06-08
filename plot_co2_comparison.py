#!/usr/bin/env python
"""Plot CO2 for ECMWF and flight observations for different levels."""
from __future__ import division

from datetime import datetime, timedelta
import os

import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from PseudoNetCDF.icarttfiles.ffi1001 import ffi1001

import common
import config


if __name__ == "__main__":
    minutes = mdates.MinuteLocator(byminute=range(0, 60, 15))
    minutes_fmt = mdates.DateFormatter('%H:%M')

    for date in config.DATES:
        start_time = datetime.strptime(date, "%Y%m%d")

        for flight in config.FLIGHTS:
            # Read flight data
            filename = config.FILENAME_FORMAT.format(flight=flight, date=date)
            f = ffi1001(os.path.join(config.DATADIR, filename))

            fco2 = f.variables[config.CO2[flight]]
            time = f.variables['UTC']
            dates = np.array([start_time + timedelta(seconds=s) for s in time])

            # Read in ECMWF flight track
            co2 = np.load("output/ecmwf_flight_tracks/{}_b200.npy"
                          .format(date))

            # Read in selected data
            sel = np.load("output/sel_levels/{}_b200.npy".format(date))

            # Get filled data
            fco2_fill = fco2.filled(np.nan)
            co2_fill = co2.filled(np.nan)

            # Plot
            fig = plt.figure(figsize=common.cm2inch(44, 26))

            nrows = len(config.LEVELS)
            ncols = 2
            gs = gridspec.GridSpec(nrows, ncols, width_ratios=[1,1])

            for k, lev in enumerate(config.LEVELS):
                # Left plot
                ax = fig.add_subplot(gs[2*k])
                s = sel[k]
                ax.plot(dates[s], fco2_fill[s], 'yo', markersize=5,
                        label="ACT")
                ax.plot(dates[s], co2_fill[s], 'ro', markersize=5,
                        label="ECMWF")

                ax.set_xlabel("Time (UTC)")
                ax.set_ylabel("CO$_2$ concentration (ppm)")

                ax.set_ylim(380, 440)
    #             ax.set_title("{} mbar".format(lev))

                if k == 0:
                    ax.legend()

                ax.xaxis.set_major_locator(minutes)
                ax.xaxis.set_major_formatter(minutes_fmt)
                ax = fig.add_subplot(gs[2*k + 1])

                # Right plot
                fco2_anom = fco2_fill[s] - np.nanmean(fco2_fill[s])
                co2_anom = co2_fill[s] - np.nanmean(co2_fill[s])

                ax.plot(fco2_anom, co2_anom, 'wo', markersize=6,
                        markeredgecolor='b', markeredgewidth=0.5)

                idx = np.isfinite(fco2_anom) & np.isfinite(co2_anom)

                p = np.polyfit(fco2_anom[idx], co2_anom[idx], 1)
                r = np.corrcoef(fco2_anom[idx], co2_anom[idx])[0,1]

                x = np.arange(-20, 20, 0.01)
                ax.plot(x, np.polyval(p, x), 'k-', alpha=0.5,
                        label="r = {:.2f}".format(r))

                ax.set_xlabel("ACT CO$_2$ concentration anomalies (ppm)")
                ax.set_ylabel("ECMWF CO$_2$ concentration anomalies (ppm)")

                ax.set_xlim(-20, 20)
                ax.set_ylim(-20, 20)

                ax.legend()

                fig.tight_layout()
                fig.savefig(common.plots() + "compare.png")

    plt.show()
