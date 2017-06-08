#!/usr/bin/env python
"""Extract flight levels specified by LEVELS in the config module.

The algorithm to extract the flight level is currently pretty crude and
is based on a threshold range for the pressure, plus a check for the pressure
change to filter out fast ascends and descends. The new data should have a flag
to extract relatively straight flight levels.
"""
from __future__ import division

from datetime import datetime, timedelta
import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from PseudoNetCDF.icarttfiles.ffi1001 import ffi1001

import common
import config


PLOT = True


def running_mean(x, N):
    csum = np.cumsum(np.insert(x, 0, 0))
    return (csum[N:] - csum[:-N]) / N


if __name__ == "__main__":
    for date in config.DATES:
        start_time = datetime.strptime(date, "%Y%m%d")

        for flight in config.FLIGHTS:
            # Read flight data
            filename = config.FILENAME_FORMAT.format(flight=flight, date=date)
            f = ffi1001(os.path.join(config.DATADIR, filename))

            mask = f.variables[config.CO2[flight]].mask

            pressure = np.ma.masked_array(f.variables['PRESSURE'], mask)
            altitude = np.ma.masked_array(f.variables['GPS_ALT'], mask)

            pressure_change = np.abs(np.diff(pressure.filled(np.nan)))
            pressure_change = pd.rolling_mean(pressure_change,
                                              config.SMOOTHING,
                                              min_periods=config.SMOOTHING//2,
                                              center=True)
            # make the diff array the same size as the original array
            pressure_change = np.r_[pressure_change, pressure_change[-1]]

            time = f.variables['UTC']
            dates = np.array([start_time + timedelta(seconds=s) for s in time])

            time = np.ma.masked_array(time, mask)
            dates = np.ma.masked_array(dates, mask)

            f.close()

            # Get levels
            sel = np.zeros((len(config.LEVELS), time.size), dtype=bool)

            for k, lev in enumerate(config.LEVELS):
                sel[k] = ((pressure < lev+config.THRES[k]) &
                          (pressure > lev-config.THRES[k]) &
                          (pressure_change < config.THRES_CHANGE))

            # Save results
            filename = "{}_{}".format(date, flight)
            np.save(os.path.join(common.output("sel_levels"), filename), sel)

            # Plot
            if PLOT:
                minutes = mdates.MinuteLocator(byminute=range(0, 60, 15))
                minutes_fmt = mdates.DateFormatter('%H:%M')

                fig = plt.figure(figsize=(8, 6,))

                ax_l = fig.add_subplot(111)
                ax_r = ax_l.twinx()

                ax_l.xaxis.grid(False)
                ax_r.xaxis.grid(False)

    #             ax_l.plot(dates, altitude, 'r')
                ax_r.plot(dates, pressure, 'b', linewidth=2)

                for k, lev in enumerate(config.LEVELS):
                    s = sel[k]
                    ax_r.plot(dates[s], pressure[s], 'r-', linewidth=2)

                    ax_r.axhline(lev, color='g', alpha=0.8)
                    ax_r.fill_between(dates, lev-config.THRES[k],
                                      lev+config.THRES[k], color='g',
                                      alpha=0.1)

                ax_l.set_ylim(altitude.min(), altitude.max())

                ax_l.xaxis.set_major_locator(minutes)
                ax_l.xaxis.set_major_formatter(minutes_fmt)

                ax_r.set_yscale('log')
                ax_r.set_yticks(config.LEVELS)
                ax_r.set_yticklabels(config.LEVELS)
                ax_r.set_ylim(pressure.max(), pressure.min())

                ax_r.set_ylabel("Pressure (mbar)")
                ax_l.set_ylabel("Approximate altitude (km)")

                plt.setp(ax_l.xaxis.get_majorticklabels(), rotation=90)

                ax_l.set_xlim(dates[0], dates[-1])

                ax_l.set_xlabel("Time (UTC)")

                fig.tight_layout()

    plt.show()
