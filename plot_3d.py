#!/usr/bin/env python
"""Plot 3D track colored by CO2."""
from __future__ import division

from datetime import datetime, timedelta
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from PseudoNetCDF.icarttfiles.ffi1001 import ffi1001

import common
import config


if __name__ == "__main__":
    for date in config.DATES:
        start_time = datetime.strptime(date, "%Y%m%d")

        for flight in config.FLIGHTS:
            # Read flight data
            filename = config.FILENAME_FORMAT.format(flight=flight, date=date)
            f = ffi1001(os.path.join(config.DATADIR, filename))

            fco2 = f.variables[config.CO2[flight]].filled(np.nan)
            ftime = f.variables['UTC']
            flats = f.variables['LATITUDE']
            flons = f.variables['LONGITUDE']
            falt = f.variables['GPS_ALT']
            fdates = np.array([start_time + timedelta(seconds=s)
                               for s in ftime])

        # Read in ECMWF
        eco2 = np.load("output/ecmwf_flight_tracks/20160804_b200.npy")
        eco2[np.isnan(fco2)] = np.nan


        ## Plot

        TITLES = [
            "ACT observations",
            "ECMWF forecast",
        ]

        # Colormap
        VMIN = 390
        VMAX = 430
        cmap = plt.get_cmap('plasma')
        norm = mpl.colors.Normalize(vmin=VMIN, vmax=VMAX)
        scalarmap = cm.ScalarMappable(norm=norm, cmap=cmap)

        fig = plt.figure(figsize=(16, 10))
        for k, co2 in enumerate([fco2, eco2]):
            ax = fig.add_subplot(1, 2, k+1, projection='3d')

            markersize = 5

            for i in range(flons.size):
                xo, yo = flons[i], flats[i]
                ho = falt[i]
                color = scalarmap.to_rgba(co2[i])

                if not np.isnan(co2[i]):
                    ax.plot([xo], [yo], [ho], 'o', markersize=markersize,
                            markerfacecolor=color, markeredgecolor='none')

            ax.set_title(TITLES[k])
            ax.set_xlabel("\n\nLongitude (deg)")
            ax.set_ylabel("\n\nLatitude (deg)")
            ax.set_zlabel("\n\nAltitude (km)")
            ax.view_init(30, 45 + 180)

            # fake up the array of the scalar mappable. Urgh...
            # (from https://stackoverflow.com/a/11558629)
            scalarmap._A = []
            cbar = plt.colorbar(scalarmap, orientation='horizontal')
            cbar.set_label("CO$_2$ concentration (ppm)")

            ax.set_xticks(np.arange(260, 268, 2))
            ax.set_yticks(np.arange(39, 44, 1))

        fig.tight_layout()
        fig.savefig(common.plots() + "plot_3d_ecmwf.png")

        plt.show()
