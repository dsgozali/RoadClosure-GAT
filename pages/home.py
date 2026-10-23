from pathlib import Path

import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st


### Missing Features -> DUE to Friday next week (30/10)
# * Ability to omit table into PDF -> (pandas <> polar (efficient way to update?)
# * Hover tooltip capability to estimate the traffic volume for weekend + weekdays (average)
# * Clickable coordinate to focus on the table view of the selected street/ region to estimate
# * Searchable map view to find where within the map is the located.
# * time slider to find the lane closure estimate of the selected time period
# * a traceability computation estimation.
# * navigation across pages to find the 

@st.cache_data
def load_road_data():
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "assets" / "QLD_CTRL" / "QLD_CTRL.shp"

    if not data_path.exists():
        return pd.DataFrame(columns=["ROAD_NAM_1", "LATITUDE", "LONGITUDE"])

    gdf = gpd.read_file(data_path)
    gdf = gdf.copy()
    if "ROAD_NAM_1" not in gdf.columns:
        for candidate in ["ROAD_NAME", "ROAD_NAM", "NAME"]:
            if candidate in gdf.columns:
                gdf = gdf.rename(columns={candidate: "ROAD_NAM_1"})
                break

    if gdf.empty:
        return pd.DataFrame(columns=["ROAD_NAM_1", "LATITUDE", "LONGITUDE"])

    if "LATITUDE" not in gdf.columns or "LONGITUDE" not in gdf.columns:
        centroids = gdf.geometry.centroid
        gdf["LONGITUDE"] = centroids.x
        gdf["LATITUDE"] = centroids.y

    return gdf


def render_home():
    st.title("Home - MapView")

    roads = load_road_data()
    if roads.empty:
        st.warning("No road geometry was found in the configured shapefile.")
        return

    map_df = roads[["ROAD_NAM_1", "LONGITUDE", "LATITUDE"]].dropna().copy()
    map_df = map_df.groupby('ROAD_NAM_1').first().reset_index()
    if map_df.empty:
        st.warning("No usable coordinates were found for the map layer.")
        return

    avg_lat = float(map_df["LATITUDE"].mean())
    avg_lon = float(map_df["LONGITUDE"].mean())

    st.pydeck_chart(
        pdk.Deck(
            map_provider="carto",
            initial_view_state=pdk.ViewState(
                latitude=avg_lat,
                longitude=avg_lon,
                zoom=6,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=map_df.to_dict(orient="records"),
                    get_position="[LONGITUDE, LATITUDE]",
                    get_radius=200,
                    get_fill_color=[230, 81, 0, 180],
                    get_line_color=[255, 255, 255, 255],
                    line_width_min_pixels=1,
                    pickable=True,
                )
            ],
            tooltip={"text": "{ROAD_NAM_1}"},
        )
    )

    st.dataframe(
        map_df.head(20).rename(columns={"ROAD_NAM_1": "Road Name", "LATITUDE": "Latitude", "LONGITUDE": "Longitude"}),
        # use_container_width=True,
        width='stretch',
        hide_index=True,
    )

