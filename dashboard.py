import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
# from shapely.geometry import Point, LineString
from streamlit_folium import folium_static
import json
import numpy as np
# from shapely.ops import nearest_points
# from pyproj import Geod
# from shapely import wkt
# from datetime import datetime, date

st.set_page_config(layout="wide")


pivotal_cols = ['ROAD_NAME', 'GAZETTAL_DIRECTION', 'HOUR']
num_cols = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN', 'WEEKEND_AVERAGE']
cols = ['SITE_ID', 'SITE_DISTANCE', 'DESCRIPTION', 'ROAD_SECTION_ID', 'LATITUDE', 'LONGITUDE', 'TDIST_START', 'TDIST_END', 'DISTRICT', 'DISTRICT_NAME', 'REGION', 'REGION_NAME']

@st.cache_data
def load_data():
    DATA_DIR = r"./data/"
    filename = "qld-traffic-data-average-by-hour-by-day-2025.xlsx"
    df = pd.read_excel(f"{DATA_DIR}{filename}")
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    df = df.groupby(pivotal_cols)[cols + num_cols].agg({
        'SITE_ID': 'first',
        'DESCRIPTION': 'sum',
        'SITE_DISTANCE': 'first',
        'ROAD_SECTION_ID': 'first',
        'TDIST_START': 'first',
        'LATITUDE': 'first',
        'LONGITUDE': 'first',
        'TDIST_END': 'first',
        'DISTRICT': 'first',
        'DISTRICT_NAME': 'first',
        'REGION': 'first',
        'REGION_NAME': 'first',
        **{col: lane_closure_logic for col in num_cols},
    }).reset_index()

    shp_path = f"{DATA_DIR}QLD_CTRL/QLD_CTRL.shp"
    gdf = gpd.read_file(shp_path)
    return df, gdf

def lane_closure_logic(x):
    return x.quantile(0.85)

# def merge_data():
#     aadt_df = load_data()
#     shp_path = "./QLD_CTRL_ROADS.shp"
#     gdf = gpd.read_file(shp_path)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

st.title('Lane Closure - General Access Time')
df, gdf = load_data()

regions = df['REGION_NAME'].unique()
districts = df['DISTRICT_NAME'].unique()#[:2]
hourly = df['HOUR'].unique()
directions = ['GAZETTAL', 'AGAINST GAZETTAL']

# Init session state for region category
if "selected_r" not in st.session_state:
    st.session_state.selected_r = None
if "selected_ds" not in st.session_state:
    st.session_state.selected_ds = None
if "selected_dow" not in st.session_state:
    st.session_state.selected_dow = num_cols
if "selected_hour" not in st.session_state:
    st.session_state.selected_hour = hourly
if "selected_road" not in st.session_state:
    st.session_state.selected_road = None
if "selected_roads_all" not in st.session_state:
    st.session_state.selected_roads_all = True

st.markdown("""
    <style>
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        font-size: 20px;
        padding: 6px;
    }
    </style>
""", unsafe_allow_html=True)

selected_regions = st.sidebar.selectbox('Select Region', regions, index=None, placeholder="Select Region...")
if not selected_regions:
    st.session_state.selected_r = None

with st.sidebar:
    for district in districts:
        if st.button(f"{district}\n\n\n{df.loc[df['DISTRICT_NAME'] == district]['DESCRIPTION'].nunique()} Roads", use_container_width=True):
            st.session_state.selected_ds = district
    if st.button("Show All", use_container_width=True):
        st.session_state.selected_ds = None

st.markdown('<div class="dow-buttons">', unsafe_allow_html=True)
dow_cols = st.columns(len(num_cols)+1)
for i, dow in enumerate(num_cols):
    if dow_cols[i].button(dow, key=f"btn_{dow}", use_container_width=True):
        st.session_state.selected_dow = [dow]
if dow_cols[-1].button("Show All", key="btn_all", use_container_width=True):
    st.session_state.selected_dow = num_cols
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="hour-buttons">', unsafe_allow_html=True)
hour_cols = st.columns(len(hourly)+1)
for i, hour in enumerate(hourly):
    if hour_cols[i].button(f"{i+1}", key=f"btn_{i}", use_container_width=True):
        st.session_state.selected_hour = [hour]
if hour_cols[-1].button("All", key="btn_hourly_all", use_container_width=True):
    st.session_state.selected_hour = hourly
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="gaz-btns">', unsafe_allow_html=True)
dir_cols = st.columns(len(directions)+1)
for i, dir in enumerate(directions):
    if dir_cols[i].button(dir, key=f"btn_dir_{i}", use_container_width=True):
        st.session_state.selected_dir = [dir]
if dir_cols[-1].button("All", key="btn_dir_all", use_container_width=True):
    st.session_state.selected_dir = directions
st.markdown('</div>', unsafe_allow_html=True)
# st.markdown('<text style={"font": "red"}>**</text>', unsafe_allow_html=True)

# Select the desired district
if st.session_state.selected_ds:
    filtered_df =  df[(df["DISTRICT_NAME"] == st.session_state.selected_ds)]
    st.write(f"**Filtered by District: {st.session_state.selected_ds}**")
else:
    if not selected_regions:
        filtered_df = df[(df["REGION_NAME"].isin(regions))]
    else:
        filtered_df = df[(df["REGION_NAME"] == selected_regions)]
        st.session_state.selected_r = selected_regions

if st.session_state.selected_hour:
    filtered_df = filtered_df[(filtered_df["HOUR"].isin(st.session_state.selected_hour))]
    # st.write(f"** Filtered by Hour {st.session_state.selected_hour}")
if st.session_state.selected_road:
    filtered_df = filtered_df[(filtered_df["ROAD_NAME"] == st.session_state.selected_road)]

user_dow = st.session_state.selected_dow

df2 = filtered_df[pivotal_cols + cols + user_dow]

search_term = st.text_input("Search by Road Name:", "")
if search_term:
    st.session_state.selected_road = search_term
    st.session_state.selected_roads_all = False

if st.session_state.selected_roads_all:
    df2 = df.copy(deep=True)
temp = df2[(df2["ROAD_NAME"].str.contains(search_term, case=False, na=False))]
if len(temp) < 1:
    temp = df2
    st.write("No such Road name exists. Please put the correct Road/ Region name")
else:
    df2 = temp

csv = convert_df(df2)

city_row = df2.iloc[0]
print(df2)
m = folium.Map(location=[city_row['LATITUDE'], city_row['LONGITUDE']], zoom_start=8)

# Marker color based on pollutant value and limit
def get_marker_color(aadt_val):
    aadt_limit = 50
    if aadt_val <= aadt_limit:
        return 'green'
    else:
        return 'red'

gdf2 = gdf[gdf.ROAD_NAM_1.isin(df2.ROAD_NAME.unique())]
nongdf2 = gdf[~(gdf.ROAD_NAM_1.isin(gdf2.ROAD_NAM_1))]
jsn = json.loads(gdf2.to_json())
for feature in jsn["features"]:
    props = feature["properties"]
    
    raw_coords = feature["geometry"]["coordinates"]
    cleaned_coords = [x[::-1] for x in raw_coords if x != [np.nan, np.nan]]
    popup_content = f"""
        <div style="font-family: sans-serif; min-width: 200px;">
            <h4>{props['ROAD_NAM_1']}</h4>
        </div>
        """
    folium.PolyLine(
        locations=cleaned_coords,
        color="#E65100",
        weight=10,
        opacity=0.8,
        popup=folium.Popup(popup_content, max_width=300),
        tooltip=f"ROAD_NAME: {props['ROAD_NAM_1']} | STREET: {props['street']} | Route Length: {props['shape_Leng']:.2f}"
    ).add_to(m)

nonjsn = json.loads(nongdf2.to_json())
for feature in nonjsn["features"]:
    props = feature["properties"]
    
    raw_coords = feature["geometry"]["coordinates"]
    cleaned_coords = [x[::-1] for x in raw_coords if x != [np.nan, np.nan]]

    popup_content = f"""
        <div style="font-family: sans-serif; min-width: 200px;">
            <h4>{props['road_name']}</h4>
        </div>
        """
    folium.PolyLine(
        locations=cleaned_coords,
        color="#000000",
        weight=4,
        opacity=0.4,
        popup=folium.Popup(popup_content, max_width=300),
        tooltip=f"ROAD_NAME: {props['road_name']} | STREET: {props['street']} | Route Length: {props['shape_Leng']:.2f}"
    ).add_to(m)

# Add markers for each city to the map
for index, row in df2.iterrows():
    folium.CircleMarker(
        location=[row['LATITUDE'], row['LONGITUDE']],
        radius=5,
        color="green",
        fill=True,
        fill_color="green",
        fill_opacity=0.7,
        tooltip=f"{row['DESCRIPTION']}: {lane_closure_logic(row[user_dow])}"
    ).add_to(m)

import time
ts = time.time()
st.download_button(
    label="Download Data as CSV",
    data=csv, 
    file_name=f"{time}_download.csv",
    mime="text/csv"
)
# Display the map 
st.subheader('Map View')
map_cols = st.columns([2,1])

with map_cols[0]:
    folium_static(m, width=1000, height=800)

with map_cols[1].container(height=850):
    st.subheader("AADT Data Summary")
    # subrows = st.columns([1,len(user_dow)])
    grouped_df = df2.groupby(['ROAD_NAME', 'GAZETTAL_DIRECTION'])[user_dow].mean().reset_index().set_index("ROAD_NAME")
    grouped_df = grouped_df.pivot(columns="GAZETTAL_DIRECTION")
    print(grouped_df)
    # st.write(grouped_df)
    # for i, row in enumerate(subrows):
    #     row[i].write(grouped_df)
    for road in grouped_df.index.unique():
        st.subheader(f"{road}")
        st.dataframe(grouped_df.loc[grouped_df.index == road].loc[:, user_dow], hide_index=True)


# Display the filtered data in a table
cols = st.columns([2,1])
with cols[0].container(width=1000):
    st.subheader('AADT Filtered Data')
with cols[1]:
    click_me = st.button("Show All", key="btn_showall", use_container_width=True)
    print(click_me)
    # df2 = df.copy(deep=True)

if click_me:
    #df2 = df.copy(deep=True)
    st.session_state.selected_roads_all = True
event = st.dataframe(df2.reset_index().drop(columns='index')[['ROAD_NAME', 'SITE_DISTANCE', 'DESCRIPTION', 'ROAD_SECTION_ID', 'TDIST_START', 'TDIST_END'] + user_dow], 
                     key='ROAD_NAME',
                     on_select="rerun",
                     selection_mode='single-row')
print(event.selection)
print(f"selection2 = {event.selection['rows']}")
row_select = event.selection['rows']
if len(row_select) > 0:
    st.session_state.selected_road = df2.reset_index().iloc[row_select]['ROAD_NAME'].iloc[0]
    st.session_state.selected_roads_all = False
else:
    st.session_state.selected_road = None
    st.session_state.selected_roads_all = True


footer_html = """
<div style='text-align: center;'>
<p>Developed by WSP - DSG </p>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)