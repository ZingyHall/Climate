#!/usr/bin/env python
"""Plot CO2 along flight track on top of shaded CO2 from ECMWF."""
from __future__ import division

from datetime import datetime, timedelta
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.basemap import Basemap
import numpy as np
import os

import netCDF4 as nc
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
            fdates = np.array([start_time + timedelta(seconds=s)
                               for s in ftime])
            sel = np.load("output/sel_levels/{}_b200.npy".format(date))[0]

        # Read in ECMWF
        ncfile = nc.Dataset("data/ecmwf_forecast/co2_{}.nc".format(date))
        co2_all = common.co2_mass2molefrac(ncfile.variables['co2'][:])
        lats = ncfile.variables['latitude'][:]
        lons = ncfile.variables['longitude'][:]
        levs = ncfile.variables['level'][:]
        time = ncfile.variables['time']
        dates = nc.num2date(time[:], time.units)

        eco2 = np.load("output/ecmwf_flight_tracks/{}_b200.npy".format(date))

        # closest forecast time to time at the middle of the flight
        closest_time = np.argmin(np.abs(dates - fdates[fdates.size//2]))
        co2 = co2_all[closest_time]


        ## Plot

        # Colormap
        VMIN = 390
        VMAX = 430
        cmap = plt.get_cmap('plasma')
        norm = mpl.colors.Normalize(vmin=VMIN, vmax=VMAX)
        scalarmap = cm.ScalarMappable(norm=norm, cmap=cmap)

        fig = plt.figure(figsize=(16, 10))
        ax = fig.add_subplot(111)

        m = Basemap(projection='cyl', llcrnrlat=38, urcrnrlat=43,
                    llcrnrlon=260, urcrnrlon=268, resolution='c')

        m.drawcoastlines(linewidth=0.5)
        m.drawmapboundary(fill_color='white')
        m.drawstates()

        longitude, latitude = np.meshgrid(lons, lats)
        x, y = m(longitude, latitude)

        m.pcolor(x, y, co2[4], cmap=cmap, vmin=VMIN, vmax=VMAX)
        cbar = m.colorbar()
        cbar.set_label("CO$_2$ concentration (ppm)")

        markersize = 4
        text_offset = 0.1

        # Plot outline
        m.plot(flons[sel], flats[sel], 'ko', markersize=markersize,
               markeredgewidth=1, latlon=True)

        time_has_been_plotted = False
        for i in range(flons[sel].size):
            xo, yo = m(flons[sel][i], flats[sel][i])
            zo = fco2[sel][i]

            # Uncomment to show ECMWF forecast "flight track" (instead of ACT
            # observations) to make sure the interpolation of ECMWF is correct
            #  zo = eco2[sel][i]

            color = scalarmap.to_rgba(zo)

            if np.isfinite(zo):
                m.plot(xo, yo, 'o', markersize=markersize,
                       markerfacecolor=color, markeredgecolor='none')

            if fdates[sel][i].minute in [0, 30]:
                if not time_has_been_plotted:
                    timeo = fdates[sel][i]
                    plt.text(xo + text_offset, yo + text_offset,
                             timeo.strftime("%H:%M UTC"), color='w',
                             fontsize=16)

                    time_has_been_plotted = True
            else:
                time_has_been_plotted = False

        fig.savefig(common.plots() + "ecmwf_contour.png")

    plt.show()
