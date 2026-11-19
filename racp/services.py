from functools import lru_cache
from io import BytesIO
import re
import itertools
from operator import itemgetter
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point, LineString
import os

import geopandas as gpd
import polars as pl
import pandas as pd
from django.conf import settings
from urllib.parse import urlencode
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Flowable
)

from .constants import DB_ALIAS, DIST_IDS, DAY_NAMES, HEADER_H, SAMPLE_ROADS, WEEKDAYS, WEEKENDS, COLOR_MAP, MARGIN, FOOTER_H
from racp.models import get_TA_volume, get_TA_volume_road, TaSite, TaPoints, TaSitePoints

PAGE_W, PAGE_H = landscape(letter)

TRAFFIC_WORKBOOK = (
    settings.BASE_DIR / "assets" / "qld-traffic-data-average-by-hour-by-day-2025.xlsx"
)
ROAD_SHAPEFILE = settings.BASE_DIR / "assets" / "QLD_CTRL" / "QLD_CTRL.shp"


def _hour_number(value):
    hour = int(value) % 24
    return hour

def ckdnearest(gdfA, gdfB, gdfB_cols=['street', 'road_name', 'carrway', 'shape_Leng', 'ROAD_NAM_1', 'DESC', 'SITE_ID']):
    A = gdfA.reset_index(drop=True).copy()
    B = gdfB.reset_index(drop=True).copy()
    A = np.concatenate(
        [np.array(geom.coords) for geom in gdfA.geometry.to_list()])
    B = [np.array(geom.coords) for geom in gdfB.geometry.to_list()]
    B_ix = tuple(itertools.chain.from_iterable(
        [itertools.repeat(i, x) for i, x in enumerate(list(map(len, B)))]))
    B = np.concatenate(B)
    ckd_tree = cKDTree(B)
    dist, idx = ckd_tree.query(A, k=1)
    idx = itemgetter(*idx)(B_ix)
    gdf = pd.concat(
        [gdfA, gdfB.loc[idx, gdfB_cols].reset_index(drop=True),
         pd.Series(dist, name='dist')], axis=1)
    return gdf

def display_hour_label(value):
    """Convert workbook hour labels to the same labels used in the matrix."""
    text = str(value).strip()
    normalized = re.fullmatch(r"(\d{1,2})\s*(?:to|-)\s*(\d{1,2})", text, re.IGNORECASE)
    if normalized:
        start, end = (_hour_number(part) for part in normalized.groups())
        end_suffix = "am" if end < 12 else "pm"
        start_display = str(start % 12 or 12)
        end_display = str(end % 12 or 12)
        if start == 11:
            end_suffix = "pm"
        elif start == 23:
            end_suffix = "am"
        return f"{start_display}-{end_display}{end_suffix}"

    normalized = re.fullmatch(
        r"(\d{1,2})(?::00)?\s*(am|pm)\s*(?:to|-)\s*(\d{1,2})(?::00)?\s*(am|pm)",
        text,
        re.IGNORECASE,
    )
    if normalized:
        start, _, end, end_period = normalized.groups()
        return f"{int(start)}-{int(end)}{end_period.lower()}"

    if re.fullmatch(r"\d{1,2}-\d{1,2}(?:am|pm)", text, re.IGNORECASE):
        return text.lower()
    return text


def _sample_traffic_data():
    rows = []
    for road_index, road in enumerate(SAMPLE_ROADS):
        for direction_index, direction in enumerate(("WB", "EB")):
            for hour in range(24):
                values = {
                    day: 250 + (road_index * 100) + (direction_index * 50) + (hour * 10) + day_index * 30
                    for day_index, day in enumerate(WEEKDAYS + WEEKENDS)
                }
                rows.append(
                    {
                        "ROAD_Details": f"AA: {road}",
                        "ROAD_NAME": road,
                        "DESCRIPTION": "Sample access",
                        "GAZETTAL_DIRECTION": direction,
                        "HOUR": f"{hour} to {(hour + 1) % 24}",
                        "REGION_NAME": "Sample Region",
                        **values,
                    }
                )
    frame = pl.DataFrame(rows)
    frame_meta = {}

    frame_meta["source"] = "Sample fallback data"
    return frame

def combine_pt(row):
    return Point(row['latitude'], row['longitude'])

@lru_cache(maxsize=1)
def load_snowflake_data(road=None, region=None, year=2025):
    """Load remote (snowflake) data for the latest one"""
    print(f"MODE!!! = {road} {region}")
    # # print("START..")
    # tasp = TaSitePoints.objects.using(DB_ALIAS['tasp'])
    # tasp_df = pl.DataFrame(list(tasp.values()), infer_schema_length=None)
    # # print(f"tasp = {tasp_df.columns}")

    # unique_sites = tasp_df['site_id_id'].unique().to_list()
    # st_points = tasp_df['start_point_id'].unique().to_list()
    # end_points = tasp_df['end_point_id'].unique().to_list()

    # tas = TaSite.objects.using(DB_ALIAS['tas']).select_related("site_id").filter(site_id__in=unique_sites).values()
    # tas_df = pl.DataFrame(list(tas.values()), infer_schema_length=None)
    # tap = TaPoints.objects.using(DB_ALIAS['tap']).select_related("point_id").exclude(latitude__isnull=True).exclude(longitude__isnull=True).filter(Q(point_id__in=st_points) | Q(point_id__in=end_points)).values()
    # tap = tap.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    # tap_df = pl.DataFrame(list(tap.values()), infer_schema_length=None)

    # tas_tasp = tasp_df.join(tas_df, left_on="site_id_id", right_on="site_id", how='inner')
    # tas_p = tas_tasp.join(tap_df, left_on="point_id_id", right_on="point_id", how="left")
    # # print(f"TASP = {tas_p.head()}")

    # # print(f"NEW WAY COLS=== {tas_p.columns}")
    # tas_p = tas_p.to_pandas()
    # tas_p = tas_p.dropna(subset=['latitude', 'longitude'])

    # tas_p['pt'] = tas_p[['latitude', 'longitude']].apply(lambda x: Point(x['latitude'], x['longitude']), axis=1)
    # # print(f"tas_p TAIL = {tas_p.tail()}")
    # # rsect_ids = list(tas_p['rsect_id'].unique())
    # # roads = pl.DataFrame()
    # # for rsect_id in rsect_ids:
    # #     road = get_DIM_static(rsect_id)
    # #     # print(f"ROAD = {road.values()}")
    # #     roads = pl.concat([roads, pl.DataFrame(list(road.values()))])

    # # # roads_geo = pl.DataFrame(roads)
    # # print(f"GEO = {roads.columns}")
    # # print(f"ROADS = {roads[0]}")

    # # print(roads_geo)
    

    # # tap = TaPoints.objects.using(DB_ALIAS['tap']).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    # # tap_df = pl.DataFrame(list(tap.values()))
    # # tap_df = tap_df.to_pandas()
    # # tap_df['pt'] = tap_df[['latitude', 'longitude']].apply(lambda x: Point(x['latitude'], x['longitude']), axis=1)

    # # print(f"COLS gpd = {gpd_pt.columns}")

    # roads = load_road_geometries()
    # # # print(gpd_pt.columns)
    # # # print(roads.columns)
    # # # print(f"pt = {gpd_pt.shape}")
    # # # print(f"ROADS = {roads.shape}")
    # # # print(roads.crs)
    # # # print(gpd_pt.crs)

    # # # # road_cols = ['street', 'road_name', 'carrway', 'shape_Leng', 'ROAD_NAM_1', 'DESC', 'SITE_ID']
    # # # pt_cols = list(gpd_pt.columns)
    # # # print(f"LIST = {pt_cols}")
    # # # # comb_gpd = gpd.sjoin_nearest(gpd_pt.to_crs("EPSG:7856"), roads.to_crs("EPSG:7856"), how="left", distance_col="dist_m")
    # # # print(comb_gpd.columns)
    # # # # comb_gpd = comb_gpd[pt_cols + road_cols].to_crs("EPSG:4326")
    # # # print("-"*60)

    # # points = list(comb_gpd['point_id'].unique())
    # # tas = TaSite.objects.using(DB_ALIAS['tas']).select_related("point_id").filter(point_id__in=points).values()
    # # tas = pl.DataFrame(list(tas), infer_schema_length=None)
    # # # print('-'*60)
    # # sites = tas['site_id'].unique().to_list()
    # # tasp = TaSitePoints.objects.using(DB_ALIAS['tasp']).select_related("site_id").filter(site_id__in=sites).values()
    # # tasp = pl.DataFrame(list(tasp), infer_schema_length=None)
    # # # print(f"TASP = {tasp}")
    # # # print('-'*60)
    # # # print(f"TAS = {tas.head()}")
    # # tas_p = tasp.join(tas, left_on="site_id_id", right_on="site_id", how='inner')
    # traff_wb = pd.read_excel(TRAFFIC_WORKBOOK)
    # # tas_p = tas_p.to_pandas()
    # # print(f"TASP = {tas_p.columns}")
    # tas_p = tas_p.merge(traff_wb[['SITE_ID', 'ROAD_NAME', 'ROAD_SECTION_ID']], left_on="site_id_id", right_on="SITE_ID", how="inner")
    # # print(f"MERGED = {tas_p.tail()}\n{tas_p.iloc[0]}")
    # gpd_pt = gpd.GeoDataFrame(tas_p, crs="EPSG:4326", geometry=tas_p['pt'])
    # gpd_pt = gpd_pt.drop(columns=['pt'])
    # # print(gpd_pt.iloc[0])
    # comb_static = ckdnearest(gpd_pt, roads)

    # # print("-"*60)
    # # print(tas_p.columns)
    # # # print(comb_gpd.columns)
    # # # print("60"*10)
    # # comb_static = comb_gpd.merge(tas_p, left_on="point_id", right_on="point_id_id", how="inner")
    # # print('-'*60 + "\nCOMB_STATIC")
    # # print(comb_static.head())
    # # print(comb_static.shape)
    # print(f"COMB_COLS = {comb_static.columns}")
    # unique_sites = list(comb_static['site_id_id'].unique())
    # # print(f"USITE are {unique_sites}")
    # ta_vol = get_TA_volume(unique_sites)

    # frame = pl.DataFrame(list(ta_vol), infer_schema_length=None)
    # frame = frame.to_pandas()
    # frame = frame.merge(comb_static[['dist_id', 'ROAD_NAME', 'ROAD_SECTION_ID', 'shape_Leng', 'site_id_id', 'site_type', 'description']], left_on="ta_road_site_id", right_on="site_id_id", how="inner")

    # return frame

    tap = TaPoints.objects.using(DB_ALIAS['tap']).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    tap_df = pl.DataFrame(list(tap.values()))
    tap_df = tap_df.to_pandas()
    tap_df['pt'] = tap_df[['latitude', 'longitude']].apply(lambda x: Point(x['latitude'], x['longitude']), axis=1)

    gpd_pt = gpd.GeoDataFrame(tap_df, crs="EPSG:4326", geometry=tap_df['pt'])
    gpd_pt = gpd_pt.drop(columns=['pt'])
    roads = load_road_geometries()
    comb_gpd = ckdnearest(gpd_pt, roads)

    points = list(comb_gpd['point_id'].unique())
    tas = TaSite.objects.using(DB_ALIAS['tas']).select_related("point_id").filter(point_id__in=points).values()
    tas = pl.DataFrame(list(tas), infer_schema_length=None)
    # print('-'*60)
    if road and region:
        dist_id = next((k for k, v in DIST_IDS.items() if v == region), None)
        tasp = TaSitePoints.objects.using(DB_ALIAS['tasp']).select_related("dist_id").filter(dist_id__in=[dist_id]).values()
        print(f"static mode = {len(tasp)}")
    else:
        sites = tas['site_id'].unique().to_list()
        tasp = TaSitePoints.objects.using(DB_ALIAS['tasp']).select_related("site_id").filter(site_id__in=sites).values()
        print(f"actual mode = {len(tasp)}")
    tasp = pl.DataFrame(list(tasp), infer_schema_length=None)
    
    tas_p = tasp.join(tas, left_on="site_id_id", right_on="site_id", how='inner')
    traff_wb = pd.read_excel(TRAFFIC_WORKBOOK)
    tas_p = tas_p.to_pandas()
    tas_p = tas_p.merge(traff_wb[['SITE_ID', 'ROAD_NAME', 'ROAD_SECTION_ID']], left_on="site_id_id", right_on="SITE_ID", how="right")

    comb_static = comb_gpd.merge(tas_p, left_on="point_id", right_on="point_id_id", how="inner")
    ta_vol = None
    if road and region:
        road = road.upper()
        comb_static = comb_static.loc[(comb_static['ROAD_NAME'] == road) | (comb_static['ROAD_SECTION_ID'] == road.split(": ")[0])]
        unique_sites = list(comb_static['site_id_id'].unique())
        ta_vol = get_TA_volume_road(unique_sites)
    else:
        unique_sites = list(comb_static['site_id_id'].unique())
        ta_vol = get_TA_volume(unique_sites)

    frame = pl.DataFrame(list(ta_vol), infer_schema_length=None)
    frame = frame.to_pandas()
    if "sum_volume" in frame.columns:
        frame['total_vol'] = frame['sum_volume']

    print(f"FRAME = {frame.head()}")
    frame = frame.merge(comb_static[['dist_id_x', 'ROAD_NAME', 'ROAD_SECTION_ID', 'shape_Leng', 'site_id_id', 'site_type', 'description_x']], left_on="ta_road_site_id", right_on="site_id_id", how="inner")

    return frame

@lru_cache(maxsize=1)
def load_traffic_data(road=None, region=None):
    """Load workbook data, falling back to a complete sample matrix schema."""
    frame_raw = load_snowflake_data(road=road, region=region)
    frame = frame_raw.rename(columns={"ta_road_site_id": "SITE_ID", 'dist_id_x':'REGION_ID', "description_x": "DESCRIPTION"})
    frame['GAZETTAL_DIRECTION'] = frame['code_t_gazettal_direction'].apply(lambda x: 'AGAINST GAZETTAL' if x == 'TA' else 'GAZETTAL')
    frame['HOUR'] = frame['hour'].apply(lambda x: f"{x} to {x+1}")
    frame['REGION_NAME'] = frame['REGION_ID'].apply(lambda x: DIST_IDS[x])
    indices = ['SITE_ID', 'code_ta_traffic_class','sk_ta_traffic_class', 'REGION_ID', 'REGION_NAME', 'HOUR', 'ROAD_SECTION_ID', 'ROAD_NAME', 'site_type', 'DESCRIPTION', 'GAZETTAL_DIRECTION']
    
    frame['total_vol'] = frame['total_vol'].apply(lambda x: int(x))
    frame2 = frame.pivot_table(index = indices, columns="day_type", values="total_vol", aggfunc="mean").reset_index()  
    frame2['ROAD_Details'] = frame2[['ROAD_SECTION_ID', 'ROAD_NAME']].apply(lambda x: f"{x['ROAD_SECTION_ID']}: {x['ROAD_NAME']}",axis=1)
    # frame2[WEEKDAYS + WEEKENDS] = (frame2[WEEKDAYS + WEEKENDS].round().astype('Int64'))
    if len(frame2) > 1:
        try:
            frame_columns = [str(column).strip() for column in frame2.columns]
            required = {
                "ROAD_NAME",
                "GAZETTAL_DIRECTION",
                "HOUR",
                "DESCRIPTION",
                *WEEKDAYS,
                *WEEKENDS,
            }
            frame = pl.from_dataframe(frame2)
            if required.issubset(set(frame_columns)):
                return frame.fill_nan(None)
        except (OSError, ValueError, ImportError) as error:
            raise RuntimeError(f"Could not read traffic workbook {TRAFFIC_WORKBOOK}") from error
    return _sample_traffic_data()
    # print("TEST!")
    # if TRAFFIC_WORKBOOK.is_file():
    #     try:
    #         frame = pd.read_excel(TRAFFIC_WORKBOOK)
    #         frame = pl.from_pandas(frame)
    #         frame.columns = [str(column).strip() for column in frame.columns]
    #         required = {
    #             "ROAD_NAME",
    #             "GAZETTAL_DIRECTION",
    #             "HOUR",
    #             "DESCRIPTION",
    #             *WEEKDAYS,
    #             *WEEKENDS,
    #         }
    #         if required.issubset(set(frame.columns)):
    #             return frame.fill_nan(None)
    #     except (OSError, ValueError, ImportError) as error:
    #         raise RuntimeError(f"Could not read traffic workbook {TRAFFIC_WORKBOOK}") from error
    # return _sample_traffic_data()


def get_regions(frame=None):
    frame = frame if frame is not None else load_traffic_data()
    if "REGION_NAME" not in frame.columns:
        return []
    return sorted(frame["REGION_NAME"].drop_nulls().unique().to_list())


def get_road_data(frame=None, region=None):
    frame = frame if frame is not None else load_traffic_data()
    if region and "REGION_NAME" in frame.columns:
        frame = frame.filter(pl.col("REGION_NAME") == region)
    return frame


def get_road_names(frame=None, region=None):
    selected = get_road_data(frame, region)
    print(f"GET_ROAD_NAMES = {selected}")
    # selected = selected.with_columns(pl.concat_str([pl.col("ROAD_SECTION_ID"), pl.lit(": "), pl.col("ROAD_NAME")], separator="").alias("ROAD_Details"))
    return sorted(selected["ROAD_Details"].drop_nulls().unique().to_list())

def lane_closure_logic(x):
    """
    To apply lane closure logic.
    """
    return x.quantile(0.85)

def _quantile(values):
    # return float(pd.Series(values, dtype="float64").quantile(0.85))
    return values.with_columns(pl.col("DAYNAMES").map_elements(lane_closure_logic))


def _lane_count(percentile):
    res = int(percentile // 1000) + 1 if percentile else 0
    return 4 if res > 4 else res


def build_matrix_group(frame, description, direction, show_volume="off"):
    """Build the weekday/Saturday/Sunday lane matrix for one road direction."""
    # subset = frame.loc[
    #     (frame["ROAD_NAME"] == road)
    #     & (frame["DESCRIPTION"] == description)
    #     & (frame["GAZETTAL_DIRECTION"] == direction)
    # ]
    subset = frame.filter(
        (pl.col("DESCRIPTION") == description) 
        & (pl.col("GAZETTAL_DIRECTION") == direction)
    ).clone()
    hours = sorted(
        subset["HOUR"].drop_nulls().unique().to_list(),
        key=lambda item: int(re.match(r"\s*(\d+)", str(item)).group(1))
        if re.match(r"\s*(\d+)", str(item))
        else 100,
    )
    if subset.is_empty():
        return [
            {
                "Direction": direction,
                "Day-HR": day,
                **{display_hour_label(hour): 1 for hour in frame["HOUR"].drop_nulls().unique()},
            }
            for day in DAY_NAMES
        ]

    rows = []
    for day in DAY_NAMES:
        columns = [day] if day in WEEKENDS else WEEKDAYS
        values = subset.with_columns(pl.concat_list(columns).alias("DAYNAMES"))
        values = values.with_columns(pl.col("DAYNAMES").map_elements(lane_closure_logic))
        row = {"Direction": direction, "Day-HR": day}
        for hour in hours:
            label = display_hour_label(hour)
            # values_frame = subset.loc[subset["HOUR"] == hour, columns]
            if hour in values['HOUR']:
                values_frame = values.filter(pl.col("HOUR") == hour).select("DAYNAMES").mean()
                # values = values_frame.to_numpy().flatten()
                # values = [value for value in values if pd.notna(value)]
                vol_item = values_frame.item()
                if show_volume == "on":
                    row[label] = vol_item if vol_item else 0
                else:
                    row[label] = _lane_count(vol_item) if vol_item else 0
            else:
                row[label] = 0
        rows.append(row)
    return rows


def build_matrix(frame, road, show_volume="off"):
    """Assemble direction matrices for every description associated with a road."""
    road_frame = frame.filter(pl.col("ROAD_Details") == road)
    descriptions = sorted(road_frame["DESCRIPTION"].drop_nulls().unique().to_list())
    directions = sorted(frame["GAZETTAL_DIRECTION"].drop_nulls().unique().to_list())
    matrices = []
    for description in descriptions:
        rows = []
        for direction in directions:
            rows.extend(build_matrix_group(road_frame, description, direction, show_volume))
        hour_columns = sorted(
            {key for row in rows for key in row if key not in {"Direction", "Day-HR"}},
            key=lambda label: next(
                (index for index, hour in enumerate(road_frame["HOUR"]) if display_hour_label(hour) == label),
                100,
            ),
        )
        matrices.append(
            {
                "description": description,
                "columns": ["Direction", "Day-HR", *hour_columns],
                "rows": rows,
            }
        )
    return matrices

def build_matrix2(frame, road, show_volume="off"):
    """Assemble direction matrices for every description associated with a road."""
    # road_frame = frame.
    road_frame = frame.filter(pl.col("ROAD_Details") == road)
    hours = sorted(road_frame["HOUR"].drop_nulls().unique().to_list())
    descriptions = sorted(road_frame["DESCRIPTION"].drop_nulls().unique().to_list())
    directions = sorted(frame["GAZETTAL_DIRECTION"].drop_nulls().unique().to_list())
    filters = {
        "days": WEEKDAYS + WEEKENDS,
        "hours": [int(hour.split(" to ")[0]) for hour in hours],
        "descriptions": descriptions,
        "directions": directions
    }
    # for description in descriptions:
    #     rows = []
    #     for direction in directions:
    #         rows.extend(build_matrix_group(road_frame, description, direction))
    #     hour_columns = sorted(
    #         {key for row in rows for key in row if key not in {"Direction", "Day-HR"}},
    #         key=lambda label: next(
    #             (index for index, hour in enumerate(road_frame["HOUR"]) if display_hour_label(hour) == label),
    #             100,
    #         ),
    #     )
    #     matrices.append(
    #         {
    #             "description": f"{road}: {description}",
    #             "columns": ["Direction", "Day-HR", *hour_columns],
    #             "rows": rows,
    #         }
    #     )
    #         # print(f"mat = {matrices}")
    return filters


def get_cell_traceability(frame, road, description, direction, day, hour):
    subset = frame.filter(
        (pl.col("ROAD_Details") == road) 
        & (pl.col("DESCRIPTION") == description)
        & (pl.col("GAZETTAL_DIRECTION") == direction)
        & (pl.col("HOUR").map_elements(display_hour_label) == hour)
    )
    
    if subset.is_empty():
        return {
            "source": "No matching source rows; the matrix fallback value is used.",
            "input_values": [],
            "percentile_85": None,
            "lane_value": 1,
        }

    columns = [day] if day in WEEKENDS else WEEKDAYS
    available = [column for column in columns if column in subset.columns]
    values = [
        value
        for column in available
        for value in subset[column].to_list()
        if value is not None
    ]
    if not values:
        return {
            "source": "No source values for this day and hour.",
            "input_values": [],
            "percentile_85": None,
            "lane_value": 0,
        }
    # values = values.with_columns(pl.concat_list(columns).alias("DAYNAMES"))
    percentile_85 = lane_closure_logic(pl.Series(values))
    lane_value = _lane_count(percentile_85) if percentile_85 else 0
    return {
        # "source": frame.attrs.get("source", "Provided traffic data"),
        "source": f"{os.getenv('SNOWFLAKE_DATABASE', 'roadclosure')} traffic values",
        "input_values": values,
        "percentile_85": percentile_85,
        "lane_value": lane_value
    }


@lru_cache(maxsize=1)
def load_road_geometries(selectedroads=None):
    if not ROAD_SHAPEFILE.is_file():
        return gpd.GeoDataFrame(columns=["ROAD_NAM_1", "LATITUDE", "LONGITUDE"])

    roads = gpd.read_file(ROAD_SHAPEFILE)
    roads = roads.copy()
    if "ROAD_NAM_1" not in roads.columns:
        for candidate in ("ROAD_NAME", "ROAD_NAM", "NAME"):
            if candidate in roads.columns:
                roads = roads.rename(columns={candidate: "ROAD_NAM_1"})
                break
    if roads.empty:
        return roads
    print(f"SELECTED = {selectedroads}")
    if selectedroads:
        selectedroads = list(selectedroads)
        roads = roads.loc[roads['ROAD_NAM_1'].isin(selectedroads)]

    if "LATITUDE" not in roads.columns or "LONGITUDE" not in roads.columns:
        if roads.crs and roads.crs.is_geographic:
            centroids = (
                roads.to_crs("EPSG:3577")
                .geometry.centroid.to_crs("EPSG:4326")
            )
        else:
            centroids = roads.geometry.centroid
            if roads.crs:
                centroids = centroids.to_crs("EPSG:4326")
        roads["LONGITUDE"] = centroids.x
        roads["LATITUDE"] = centroids.y
    return roads


def build_map_points(frame, region=None):
    traffic = get_road_data(frame, region)
    roads = load_road_geometries()
    if roads.empty or "ROAD_NAM_1" not in roads.columns:
        return []

    weekday_columns = [column for column in WEEKDAYS if column in traffic.columns]
    if not weekday_columns or not {"SAT", "SUN"}.issubset(traffic.columns):
        return []
    traffic = traffic.clone()
    # traffic["_weekday_average"] = traffic[weekday_columns].mean()
    traffic = traffic.with_columns(pl.mean_horizontal(weekday_columns).alias("_weekday_average"))

    group_columns = ["ROAD_NAME", "ROAD_SECTION_ID"]
    if "SITE_ID" in traffic.columns:
        group_columns.insert(0, "SITE_ID")
    
    averages = traffic.group_by(group_columns).agg(
        pl.mean_horizontal(weekday_columns).mean().alias("Weekdays"),
        pl.col("SAT").mean().alias("Saturday"),
        pl.col("SUN").mean().alias("Sunday")
    )
    averages = averages.to_pandas()
    roads = roads.merge(averages, on="SITE_ID", how="inner")
    roads = roads.groupby("ROAD_NAM_1", as_index=False).first()
    points = []
    for _, row in roads.dropna(subset=["LATITUDE", "LONGITUDE"]).drop_duplicates("ROAD_NAM_1").iterrows():
        query = urlencode(
            {
                "road": f"{row['ROAD_SECTION_ID']}: {row['ROAD_NAM_1']}"
            }
        )
        points.append(
            {
                "road": f"{row['ROAD_SECTION_ID']}: {row['ROAD_NAM_1']}",
                "latitude": float(row["LATITUDE"]),
                "longitude": float(row["LONGITUDE"]),
                "weekdays": round(float(row["Weekdays"]), 2),
                "saturday": round(float(row["Saturday"]), 2),
                "sunday": round(float(row["Sunday"]), 2),
                "url": f"{reverse('racp:matrix')}?{query}" if query else "",
            }
        )
    return points

def parse_lanes(value):
    """Parse a lane count from a string or numeric value."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(str(value).strip())
    except (ValueError, TypeError):
        return None

    if number.is_integer():
        return int(number)
    return None

class RoadMarker(Flowable):
    def __init__(self, road_id, road_name):
        super().__init__()
        self.road_id = road_id
        self.road_name = road_name
        
    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        self.canv._road_header = (self.road_id, self.road_name)

def draw_header_footer(canvas, doc):
    canvas.saveState()
    top_y = PAGE_H - MARGIN + 6
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(MARGIN, top_y - 10, f"No of lanes to keep open")

    box_w, box_h = 30, 14
    x = MARGIN + 125
    for level in range(1, 5):
        color = colors.HexColor(COLOR_MAP.get(level, "#ffffff"))
        canvas.setFillColor(color)
        canvas.setStrokeColor(colors.HexColor("#dfe3e8"))
        canvas.rect(x, top_y - 14, box_w, box_h, fill=1, stroke=1)
        canvas.setFillColor(colors.white if level == 4 else colors.black)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(x + box_w / 2, top_y - 10, str(level))
        x += box_w

    road_id, road_name = getattr(canvas, "_road_header", ("", ""))
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawRightString(PAGE_W - MARGIN, top_y - 10, f"ID: {road_id} Road: {road_name}".strip())

    canvas.setStrokeColor(colors.HexColor("#1f3f5f"))
    canvas.setLineWidth(1)
    canvas.line(MARGIN, top_y - 20, PAGE_W - MARGIN, top_y - 20)

    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 4, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()

def create_matrix_pdf(matrices, road=None):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=24,
        rightMargin=24,
        topMargin=30,
        bottomMargin=30,
        title="Road closure access matrix",
    )
    styles = getSampleStyleSheet()
    dirs = {"AGAINST GAZETTAL": "WB", "GAZETTAL": "EB"}
    content = [Paragraph("General Access Times", styles["Title"]), Spacer(1, 12)]
    for matrix in matrices:
        content.append(Paragraph(f"{road or 'All roads'} - {matrix['description']}", styles["Heading2"]))
        table_data = [matrix["columns"]]
        table_data.extend([[dirs[row.get(column, "")] if row.get(column, "") in dirs.keys() else row.get(column, "") for column in matrix["columns"]] for row in matrix["rows"]])
        table_width = landscape(letter)[0] - 48
        column_width = table_width / max(len(matrix["columns"]), 1)
        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[column_width] * len(matrix["columns"]),
        )
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3f5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dfe3e8")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]

        for r, row in enumerate(table_data[1:], start=1):
            for c, cell in enumerate(row):
                level = parse_lanes(cell)
                if level is None:
                    continue
                bg = colors.HexColor(COLOR_MAP.get(level, "#ffffff"))
                style_commands.append(("BACKGROUND", (c, r), (c, r), bg))
                if level == 4:
                    style_commands.append(("TEXTCOLOR", (c, r), (c, r), colors.white))
        table.setStyle(TableStyle(style_commands))
        content.extend((table, Spacer(1, 14)))
    document.build(content)
    buffer.seek(0)
    return buffer

def dataframe_to_pdf(dataframe, road=None):
    """
    Convert a pandas DataFrame to a PDF in memory.
    Returns BytesIO object containing PDF data.
    """
    buffer = BytesIO()

    document = BaseDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="DataFrame Export",
    )

    frame_width = PAGE_W - 2 * MARGIN
    frame = Frame(
        MARGIN,
        MARGIN + FOOTER_H,
        frame_width,
        PAGE_H - 2 * MARGIN - HEADER_H - FOOTER_H,
        id="main",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
    )

    document.addPageTemplates([PageTemplate(id="main", frames=[frame], onPageEnd=draw_header_footer)])

    styles = getSampleStyleSheet()

    def road_info(matrix):
        return (
            matrix.get("road_id", ""),
            matrix.get("road_name", road or "All roads"),
        )

    content = []
    if dataframe:
        content.append(RoadMarker(*road_info(dataframe[0])))

    content.extend([Paragraph("Road Closure Access Matrix", styles["Title"]), Spacer(1, 12)])
    dirs = {"AGAINST GAZETTAL": "WB", "GAZETTAL": "EB"}
    prev_road = None
    for idx, mat in enumerate(dataframe):
        road_id, road_name = road_info(mat)
        current_road = (road_id, road_name)

        if idx > 0 and current_road != prev_road:
            content.append(PageBreak())
            content.append(RoadMarker(road_id, road_name))
        prev_road = current_road

        content.append(Paragraph(f"{road_name} - {mat.get('description', '')}", styles["Heading2"]))
        # table_data = [mat.get("columns", [])] + mat.get("rows", [])
        table_data = [mat.get("columns", [])]
        table_data.extend([[dirs[row.get(column, "")] if row.get(column, "") in dirs.keys() else row.get(column, "") for column in mat["columns"]] for row in mat["rows"]])
        # table_width = landscape(letter)[0] - 2 * MARGIN
        table_width = landscape(letter)[0] - 48
        column_width = table_width / max(len(mat.get("columns", [])), 1)
        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[column_width] * len(mat.get("columns")),
        )
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3f5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dfe3e8")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]

        for r, row in enumerate(table_data[1:], start=1):
            for c, cell in enumerate(row):
                level = parse_lanes(cell)
                if level is None:
                    continue
                bg = colors.HexColor(COLOR_MAP.get(level, "#ffffff"))
                style_commands.append(("BACKGROUND", (c, r), (c, r), bg))
                if level == 4:
                    style_commands.append(("TEXTCOLOR", (c, r), (c, r), colors.white))
        table.setStyle(TableStyle(style_commands))
        content.extend((table, Spacer(1, 14)))

    document.build(content)
    buffer.seek(0)
    return buffer
    ####################################################################
    # c = canvas.Canvas(buffer, pagesize=letter)
    # width, height = letter

    # # Title
    # c.setFont("Helvetica-Bold", 14)
    # c.drawString(50, height - 50, "DataFrame Export")

    # # Table header
    # c.setFont("Helvetica-Bold", 12)
    # y = height - 80
    # for col in dataframe.columns:
    #     c.drawString(50 + dataframe.get_column_index(col) * 150, y, str(col))

    # # Table rows
    # c.setFont("Helvetica", 12)
    # for row in dataframe.iter_rows(named=True):
    #     y -= 20
    #     for col in dataframe.columns:
    #         c.drawString(50 + dataframe.get_column_index(col) * 150, y, str(row[col]))

    # c.showPage()
    # c.save()
    # buffer.seek(0)
    # return buffer
