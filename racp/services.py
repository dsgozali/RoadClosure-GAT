from functools import lru_cache
from io import BytesIO
import re

import geopandas as gpd
import polars as pl
import pandas as pd
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .constants import DAY_NAMES, SAMPLE_ROADS, WEEKDAYS, WEEKENDS


TRAFFIC_WORKBOOK = (
    settings.BASE_DIR / "assets" / "qld-traffic-data-average-by-hour-by-day-2025.xlsx"
)
ROAD_SHAPEFILE = settings.BASE_DIR / "assets" / "QLD_CTRL" / "QLD_CTRL.shp"


def _hour_number(value):
    hour = int(value) % 24
    return hour


def display_hour_label(value):
    """Convert workbook hour labels to the same labels used in the matrix."""
    text = str(value).strip()
    normalized = re.fullmatch(r"(\d{1,2})\s*(?:to|-)\s*(\d{1,2})", text, re.IGNORECASE)
    if normalized:
        start, end = (_hour_number(part) for part in normalized.groups())
        start_suffix = "am" if start < 12 else "pm"
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
                        "ROAD_NAME": road,
                        "DESCRIPTION": "Sample access",
                        "GAZETTAL_DIRECTION": direction,
                        "HOUR": f"{hour} to {(hour + 1) % 24}",
                        "REGION_NAME": "Sample Region",
                        **values,
                    }
                )
    frame = pl.DataFrame(rows)
    frame.attrs["source"] = "Sample fallback data"
    return frame


@lru_cache(maxsize=1)
def load_traffic_data():
    """Load workbook data, falling back to a complete sample matrix schema."""
    if TRAFFIC_WORKBOOK.is_file():
        try:
            frame = pd.read_excel(TRAFFIC_WORKBOOK)
            frame = pl.from_pandas(frame)
            frame.columns = [str(column).strip() for column in frame.columns]
            required = {
                "ROAD_NAME",
                "GAZETTAL_DIRECTION",
                "HOUR",
                "DESCRIPTION",
                *WEEKDAYS,
                *WEEKENDS,
            }
            if required.issubset(set(frame.columns)):
                return frame.fill_nan(None)
        except (OSError, ValueError, ImportError) as error:
            raise RuntimeError(f"Could not read traffic workbook {TRAFFIC_WORKBOOK}") from error
    return _sample_traffic_data()


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
    return sorted(selected["ROAD_NAME"].drop_nulls().unique().to_list())

def lane_closure_logic(x):
    """
    To apply lane closure logic.
    """
    return x.quantile(0.85)

def _quantile(values):
    # return float(pd.Series(values, dtype="float64").quantile(0.85))
    return values.with_columns(pl.col("DAYNAMES").map_elements(lane_closure_logic))


def _lane_count(percentile):
    return int(percentile // 1000) + 1 if percentile else 0


def build_matrix_group(frame, description, direction):
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
                row[label] = _lane_count(vol_item) if vol_item else 0
            else:
                row[label] = 0
        rows.append(row)
    return rows


def build_matrix(frame, road):
    """Assemble direction matrices for every description associated with a road."""
    road_frame = frame.filter(pl.col("ROAD_NAME") == road)
    descriptions = sorted(road_frame["DESCRIPTION"].drop_nulls().unique().to_list())
    directions = sorted(frame["GAZETTAL_DIRECTION"].drop_nulls().unique().to_list())
    matrices = []
    for description in descriptions:
        rows = []
        for direction in directions:
            rows.extend(build_matrix_group(road_frame, description, direction))
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

def build_matrix2(frame):
    """Assemble direction matrices for every description associated with a road."""
    # road_frame = frame.
    road_frame = frame.clone()
    roads = sorted(road_frame["ROAD_NAME"].drop_nulls().unique().to_list())
    descriptions = sorted(road_frame["DESCRIPTION"].drop_nulls().unique().to_list())
    directions = sorted(frame["GAZETTAL_DIRECTION"].drop_nulls().unique().to_list())
    matrices = []
    for road in roads:
        for description in descriptions:
            rows = []
            for direction in directions:
                rows.extend(build_matrix_group(road_frame, description, direction))
            hour_columns = sorted(
                {key for row in rows for key in row if key not in {"Direction", "Day-HR"}},
                key=lambda label: next(
                    (index for index, hour in enumerate(road_frame["HOUR"]) if display_hour_label(hour) == label),
                    100,
                ),
            )
            matrices.append(
                {
                    "description": f"{road}: {description}",
                    "columns": ["Direction", "Day-HR", *hour_columns],
                    "rows": rows,
                }
            )
            # print(f"mat = {matrices}")
    return matrices


def get_cell_traceability(frame, road, description, direction, day, hour):
    subset = frame.filter(
        (pl.col("ROAD_NAME") == road) 
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
        "source": "Workbook traffic values",
        "input_values": values,
        "percentile_85": percentile_85,
        "lane_value": lane_value
    }


@lru_cache(maxsize=1)
def load_road_geometries():
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
    print('-'*60)
    print(traffic)
    print('-'*60)
    # traffic["_weekday_average"] = traffic[weekday_columns].mean()
    traffic = traffic.with_columns(pl.mean_horizontal(weekday_columns).alias("_weekday_average"))
    print("\\"*60)
    print(traffic)
    group_columns = ["ROAD_NAME"]
    if "SITE_ID" in traffic.columns:
        group_columns.insert(0, "SITE_ID")
    averages = traffic.group_by(group_columns).agg(
        pl.mean_horizontal(weekday_columns).mean().alias("Weekdays"),
        pl.col("SAT").mean().alias("Saturday"),
        pl.col("SUN").mean().alias("Sunday")
    )
    averages = averages.to_pandas()
    roads = roads.merge(averages, left_on="ROAD_NAM_1", right_on="ROAD_NAME", how="inner")
    roads = roads.groupby("ROAD_NAM_1", as_index=False).first()
    points = []
    for _, row in roads.dropna(subset=["LATITUDE", "LONGITUDE"]).drop_duplicates("ROAD_NAM_1").iterrows():
        points.append(
            {
                "road": str(row["ROAD_NAM_1"]),
                "latitude": float(row["LATITUDE"]),
                "longitude": float(row["LONGITUDE"]),
                "weekdays": round(float(row["Weekdays"]), 2),
                "saturday": round(float(row["Saturday"]), 2),
                "sunday": round(float(row["Sunday"]), 2),
            }
        )

    return points


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
    content = [Paragraph("Road Closure Access Matrix", styles["Title"]), Spacer(1, 12)]
    for matrix in matrices:
        content.append(Paragraph(f"{road or 'All roads'} - {matrix['description']}", styles["Heading2"]))
        table_data = [matrix["columns"]]
        table_data.extend([[row.get(column, "") for column in matrix["columns"]] for row in matrix["rows"]])
        table_width = landscape(letter)[0] - 48
        column_width = table_width / max(len(matrix["columns"]), 1)
        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[column_width] * len(matrix["columns"]),
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3f5f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dfe3e8")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
                ]
            )
        )
        content.extend((table, Spacer(1, 14)))
    document.build(content)
    buffer.seek(0)
    return buffer

def dataframe_to_pdf(dataframe):
    """
    Convert a pandas DataFrame to a PDF in memory.
    Returns BytesIO object containing PDF data.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "DataFrame Export")

    # Table header
    c.setFont("Helvetica-Bold", 12)
    y = height - 80
    for col in dataframe.columns:
        c.drawString(50 + dataframe.get_column_index(col) * 150, y, str(col))

    # Table rows
    c.setFont("Helvetica", 12)
    for row in dataframe.iter_rows(named=True):
        y -= 20
        for col in dataframe.columns:
            c.drawString(50 + dataframe.get_column_index(col) * 150, y, str(row[col]))

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
