#!/usr/bin/env python
"""Get data from ECMWF corresponding to the observations from the flights.

Use the closest two forecast times (before and after the flight) and
perform linear interpolation in the horizontal and log-linear interpolation
between the closest two pressure levels.
"""
from __future__ import division

from datetime import datetime, timedelta
import os

import netCDF4 as nc
import numpy as np
from scipy import interpolate

from PseudoNetCDF.icarttfiles.ffi1001 import ffi1001

import common
import config


def level_above_below(pressure, levels):
    """Find pressure level above and below the given ``pressure`` level.

    Assumes that ``levels`` goes from lower to higher pressures.
    If greater/lesser or equal to ``levels`` range, return  max/min of
    ``levels``.
    """
    levels_max = levels.max()
    levels_min = levels.min()

    if pressure >= levels_max:
        return -1, -1
    elif pressure <= levels_min:
        return 0, 0

    levels_above = (levels < pressure)
    first_level_above = np.where(levels_above == True)[0][-1]

    return first_level_above, first_level_above+1


if __name__ == "__main__":
    for date in config.DATES:
        start_time = datetime.strptime(date, "%Y%m%d")

        for flight in config.FLIGHTS:
            # Read flight data
            filename = config.FILENAME_FORMAT.format(flight=flight, date=date)
            f = ffi1001(os.path.join(config.DATADIR, filename))

            flons = f.variables['LONGITUDE']
            flats = f.variables['LATITUDE']
            flevs = f.variables['PRESSURE']
            ftime = f.variables['UTC']
            fco2 = f.variables[config.CO2[flight]]
            fdates = np.array([start_time + timedelta(seconds=s)
                               for s in ftime])

            f.close()

        # Read in ECMWF
        ncfile = nc.Dataset("data/ecmwf_forecast/co2_{}.nc".format(date))
        co2_all = common.co2_mass2molefrac(ncfile.variables['co2'][:])
        lats = ncfile.variables['latitude'][:]
        lons = ncfile.variables['longitude'][:]
        levs = ncfile.variables['level'][:]
        time = ncfile.variables['time']
        dates = nc.num2date(time[:], time.units)

        # closest forecast time to time at the middle of the flight
        closest_time = np.argmin(np.abs(dates - fdates[fdates.size//2]))
        co2 = co2_all[closest_time]

        # Interpolate ECMWF to flight track
        x, y = np.meshgrid(lons, lats)
        interp = [
            interpolate.RectBivariateSpline(lats[::-1], lons, co2[i,::-1,:])
            for i in range(levs.size)
        ]

        ecmwf_flight = np.zeros(fco2.shape)
        for t in range(ftime.size):
            above, below = level_above_below(flevs[t], levs)

            co2_above = np.squeeze(interp[above](flats[t], flons[t]))
            co2_below = np.squeeze(interp[below](flats[t], flons[t]))

            ecmwf_flight[t] = np.interp(flevs[t], [levs[above], levs[below]],
                                        [co2_above, co2_below])

        ecmwf_flight = np.ma.masked_array(ecmwf_flight, fco2.mask)

        outdir = common.output("ecmwf_flight_tracks")
        filename = "{}_{}.npy".format(date, flight)
        np.ma.dump(ecmwf_flight, os.path.join(outdir, filename))
