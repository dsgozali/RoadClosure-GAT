
# TARGET_COUNTRY = "Japan"
EXTERNAL_API = None
WEBSITE_TITLE = "Road Access Closure Permit (RACP)"
DARK_THEME = "mantine_dark"
LIGHT_THEME = "mantine_light"

Work_DIR = r"..\\assets\\"
filename = "qld-traffic-data-average-by-hour-by-day-2025.xlsx"
shp_path = "QLD_CTRL/QLD_CTRL.shp"

centerpt = [-27.454178165442357, 153.03858515277315]
groups = 20
pivotal_cols = ['ROAD_NAME', 'GAZETTAL_DIRECTION', 'HOUR']
num_cols = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN', 'WEEKEND_AVERAGE']

day_names = ["Weekday", "SAT", "SUN"]
weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI']
weekends = day_names[1:]

cols = ['SITE_ID', 'SITE_DISTANCE', 'DESCRIPTION', 'ROAD_SECTION_ID', 'LATITUDE', 'LONGITUDE', 'TDIST_START', 'TDIST_END', 'DISTRICT', 'DISTRICT_NAME', 'REGION', 'REGION_NAME']

hour_to_pm = {x: i for i, x in enumerate(range(13, 25), start=1)}
COLOR_MAP = {
    1: "#dfeef8",
    2: "#e9dcc6",
    3: "#f7b267",
    4: "#d9534f",
}

HOUR_LABELS = [
    "12-1am", "1-2am", "2-3am", "3-4am", "4-5am", "5-6am",
    "6-7am", "7-8am", "8-9am", "9-10am", "10-11am", "11-12pm",
    "12-1pm", "1-2pm", "2-3pm", "3-4pm", "4-5pm", "5-6pm",
    "6-7pm", "7-8pm", "8-9pm", "9-10pm", "10-11pm", "11-12am",
]

LEGEND_TEXT = "Legend: 1 = light blue, 2 = light brown, 3 = orange, 4 = red. Additional notes: lane openings increase with congestion pressure and represent the access-window intensity used for the operational review."


# GRAPH_TITLES = {
#     "gdp_growth": "GDP Growth [%]",
#     "gdp_nominal": "Nominal GDP",
#     "gdp_per_capita_nominal": "Nominal per capita GDP",
#     "gdp_per_capita_ppp": "Nominal per capita GDP PPP",
#     "Life Expectancy": "Life Expectancy [Years]",
#     "Population": "Population [Millions]",
#     "GDP per Capita": "GDP per Capita",
# }
# GRAPH_DESCRIPTIONS = {
#     "gdp_growth": "Current and historical GDP (Gross Domestic Product) percentage growth",
#     "gdp_nominal": "Current and historical GDP (Gross Domestic Product)",
#     "gdp_per_capita_nominal": "Current and historical GDP (Gross Domestic Product) per capita",
#     "gdp_per_capita_ppp": "Current and historical GDP (Gross Domestic Product) per capita PPP (Purchasing Power Parity)",
#     "Life Expectancy": "Current and historical life Expectancy in years",
#     "Population": "Current and historical population in millions of people",
#     "GDP per Capita": "Current and historical GDP (Gross Domestic Product) per capita",
# }
