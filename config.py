import math


DATES = (
    '20160804',
)

FLIGHTS = (
#     'c130',
    'b200',
)

DATADIR = "data/flight_data"
FILENAME_FORMAT = "ACTAMERICA-mrg05-{flight}_merge_{date}_RB.ict"

CO2 = {
    'c130': "CO2_MixingRatio_PICARRO",
    'b200': "CO2_PICARRO",
}

LEVELS = [
    925,
]

# Threshold range choosing a flight level, scaled by the pressure
BASE_THRESHOLD = 20  # mbar
THRES = [BASE_THRESHOLD*math.exp(lev/1000.) for lev in LEVELS]

# Filtering out fast ascends and descends
SMOOTHING = 12 * 5  # *5 seconds
THRES_CHANGE = 1.0  # mbar/5s
