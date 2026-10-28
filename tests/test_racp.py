from pathlib import Path

import pandas as pd
import polars as pl
import pytest

from pages.home import load_road_data
from pages.matrix import _build_matrix_group, _get_cell_traceability
from utils.apis import _load_matrix_df, lane_closure_logic
from utils.consts import HOUR_LABELS
from utils.miscs import format_hour


def test_load_matrix_df_returns_expected_data_frame():
    df = _load_matrix_df()

    assert isinstance(df, pl.DataFrame)
    assert {"ROAD_NAME", "GAZETTAL_DIRECTION", "HOUR"}.issubset(set(df.columns))
    assert len(df) > 0


def test_load_matrix_df_falls_back_when_excel_is_missing(monkeypatch):
    real_exists = Path.exists

    def fake_exists(self):
        if str(self).endswith("qld-traffic-data-average-by-hour-by-day-2025.xlsx"):
            return False
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)

    df = _load_matrix_df()

    assert isinstance(df, pl.DataFrame)
    assert {"ROAD_NAME", "GAZETTAL_DIRECTION", "DAY_HR", "HOUR", "VALUE"}.issubset(set(df.columns))
    assert len(df) > 0
    assert "Aster Road" in df["ROAD_NAME"].to_list()


def test_load_road_data_returns_empty_schema_when_shapefile_is_missing(monkeypatch):
    real_exists = Path.exists

    def fake_exists(self):
        if str(self).endswith("QLD_CTRL.shp"):
            return False
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)

    roads = load_road_data()

    assert isinstance(roads, pl.DataFrame)
    assert roads.columns == ["ROAD_NAM_1", "LATITUDE", "LONGITUDE"]
    assert roads.empty


def test_lane_closure_logic_matches_85th_percentile():
    values = pd.Series([10, 20, 30, 40, 100])

    result = lane_closure_logic(values)

    assert result == pytest.approx(values.quantile(0.85))


def test_format_hour_maps_standard_times_correctly():
    assert format_hour("0", 0) == "12"
    assert format_hour("0", 1) == "12pm"
    assert format_hour("1", 0) == "1"
    assert format_hour("1", 1) == "1am"
    assert format_hour("13", 0) == "1"
    assert format_hour("13", 1) == "1pm"


def test_build_matrix_group_generates_expected_day_rows():
    sample = pl.DataFrame(
        {
            "DESCRIPTION": ["Access to CBD", "Access to CBD"],
            "ROAD_NAME": ["Aster Road", "Aster Road"],
            "GAZETTAL_DIRECTION": ["WB", "WB"],
            "HOUR": ["12-1am", "1-2am"],
            "MON": [100, 200],
            "TUE": [120, 220],
            "WED": [130, 230],
            "THU": [140, 240],
            "FRI": [150, 250],
            "SAT": [300, 400],
            "SUN": [350, 450],
        }
    )

    matrix = _build_matrix_group("Access to CBD", "WB", sample, HOUR_LABELS[:2])

    assert matrix["Direction"].to_list() == ["WB", "WB", "WB"]
    assert matrix["Day-HR"].to_list() == ["Weekday", "SAT", "SUN"]
    assert set(matrix.columns) >= {"Direction", "Day-HR", "12-1am", "1-2am"}
    assert matrix["12-1am"].to_list() != [0, 0, 0]


def test_cell_traceability_reports_weekday_inputs_and_lane_calculation():
    sample = pl.DataFrame(
        {
            "ROAD_NAME": ["Aster Road"],
            "DESCRIPTION": ["Access to CBD"],
            "GAZETTAL_DIRECTION": ["WB"],
            "HOUR": ["0 to 1"],
            "MON": [100],
            "TUE": [200],
            "WED": [300],
            "THU": [400],
            "FRI": [500],
            "SAT": [600],
            "SUN": [700],
        }
    )

    trace = _get_cell_traceability(
        sample,
        "Aster Road",
        "Access to CBD",
        "WB",
        "Weekday",
        "12-1am",
    )

    assert trace["source"] == "Workbook traffic values"
    assert trace["input_values"] == [100, 200, 300, 400, 500]
    assert trace["percentile_85"] == lane_closure_logic(pl.Series([100, 200, 300, 400, 500]))
    assert trace["lane_value"] == int(trace["percentile_85"] // 1000) + 1
