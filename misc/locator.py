import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import numpy as np

DATA_DIR = r"./"
filename = "qld-traffic-data-average-by-hour-by-day-2025.xlsx"

def transform_pt_road(x):
    coords = list(dict.fromkeys(x.tolist()))
    # print(coords)
    return LineString(coords) if len(coords) > 1 else LineString(coords*2) if len(coords) > 0 else None

# Load Data
df = pd.read_excel(f"{DATA_DIR}{filename}")
df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
# Generate a Point shape
df['pt'] = df[['LATITUDE', 'LONGITUDE']].apply(lambda x: Point(x['LATITUDE'], x['LONGITUDE']), axis=1)

# Generate a Road Linestring
test = df.copy(deep=True)
combine_df = df.groupby(['ROAD_NAME', 'GAZETTAL_DIRECTION']).agg(
    ROADLINE=('pt', transform_pt_road),
    TDIST_START=('TDIST_START', 'mean'),
    TDIST_END=('TDIST_END', 'mean')
).reset_index()

gdf = gpd.GeoDataFrame(combine_df, crs='EPSG:4326', geometry=combine_df.ROADLINE)
gdf = gdf.drop(columns=['ROADLINE'])
# Save to a file
gdf.to_file("QLD_CTRL_ROADS.shp")