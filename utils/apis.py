import pandas as pd
import polars as pl
from pathlib import Path
import streamlit as st

from utils.consts import HOUR_LABELS, groups, filename, pivotal_cols, cols, num_cols

DEBUG = False

## logic 
def lane_closure_logic(x):
    """
    To apply lane closure logic.
    """
    return x.quantile(0.85)

def fetch_local_data():
    """
    Fetch locally store data from the AADT 2025 as a placeholder.
    Return:
        Return the header and value dataframe.
    """
    if DEBUG:
        header_df = pd.DataFrame()
        values_df = pd.DataFrame()
    else:
        df = pd.read_excel(f".{dash.get_asset_url(filename)}")
        df = df.loc[(df['REGION_NAME'] == "Metropolitan")]
        roads50 = df['ROAD_NAME'].unique()
        df = df.loc[df['ROAD_NAME'].isin(roads50[:groups])]
        print(f"SHJAPE = {df.shape}")
        header_df = df.groupby(pivotal_cols[:2])[cols].agg({
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
        }).reset_index()

        values_df = df.groupby(pivotal_cols)[num_cols].agg({
            **{col: lane_closure_logic for col in num_cols}
        }).reset_index()
    
    return header_df, values_df

def fetch_remote_data():
    """
    Fetch data from the cloud (Snowflake)
    Precondition:
        - Be sure to preset the Snowflake .env and .config with your ADM and TMR username.

    Return:
        Return Header and Value dataframe.
    """
    return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def _load_matrix_df():
    project_root = Path(__file__).resolve().parents[1]
    workbook_path = project_root / "assets" / "qld-traffic-data-average-by-hour-by-day-2025.xlsx"

    if workbook_path.exists():
        try:
            df = pd.read_excel(workbook_path)
            df = pl.from_pandas(df)
            df = df.head(5000)
            df.columns = [str(col).strip() for col in df.columns]
            if {"ROAD_NAME", "GAZETTAL_DIRECTION", "HOUR"}.issubset(set(df.columns)):
                return df
        except Exception:
            pass
    rows = []
    street_names = ["Aster Road", "Cedar Avenue", "Hawthorn Street", "Mango Crescent", "River Place"]
    directions = ["WB", "EB"]
    day_names = ["Weekday", "Saturday", "Sunday"]
    for street_idx, street_name in enumerate(street_names):
        for direction in directions:
            direction_offset = 0 if direction == "WB" else 1
            for day_idx, day_name in enumerate(day_names):
                values = []
                for hour_idx in range(len(HOUR_LABELS)):
                    base = ((street_idx + 1) * 2 + direction_offset + day_idx + hour_idx) % 4
                    values.append((base % 4) + 1)
                rows.append({
                    "ROAD_NAME": street_name,
                    "GAZETTAL_DIRECTION": direction,
                    "DAY_HR": day_name,
                    "HOUR": HOUR_LABELS[0],
                    "VALUE": values,
                })

    # df = pd.DataFrame(rows)
    df = pl.DataFrame(rows)
    print("WHATS>?!")
    return df
    
