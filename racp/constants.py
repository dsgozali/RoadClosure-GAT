"""Django-side copy of the display and calculation constants."""

DAY_NAMES = ["Weekday", "SAT", "SUN"]
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI"]
WEEKENDS = ["SAT", "SUN"]
COLOR_MAP = {
    1: "#dfeef8",
    2: "#e9dcc6",
    3: "#f7b267",
    4: "#d9534f",
}

DB_ALIAS = {
    "tas": "SW_SITE",
    "tap": "SW_SITE",
    "tasp": "SW_SITE",
    "ta_vol": "TA_VOL",
}

DIST_IDS = {
    401: "Central West",
    402: "Darling Dows",
    403: "Far North",
    404: "Fitzroy",
    405: "Mackay/ Whitsunday",
    406: "Metropolitan",
    407: "North Coast",
    408: "Northern",
    409: "North West",
    410: "South Coast",
    411: "South West",
    412: "Wide Bay/ Burnett"
}


HEADER_H = 34
FOOTER_H = 26
MARGIN = 24

LEGEND_TEXT = (
    "Legend: 1 = light blue, 2 = light brown, 3 = orange, 4 = red. "
)
SAMPLE_ROADS = [
    "Aster Road",
    "Cedar Avenue",
    "Hawthorn Street",
    "Mango Crescent",
    "River Place",
]

