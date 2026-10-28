# import pandas as pd
import polars as pl
import streamlit as st
from pandas.io.formats.style import Styler
from great_tables import style, loc, GT


from utils.consts import COLOR_MAP, LEGEND_TEXT, HOUR_LABELS, hour_to_pm, day_names, weekdays, weekends
from utils.miscs import format_hour, export_df_to_pdf
from utils.apis import lane_closure_logic, _load_matrix_df

def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def apply_value_coloring(df, columns, color_map):
    """Applies dynamic cell backgrounds and text styles based on cell values."""
    columns = list(columns)

    display_df = df.select([
        "Direction",
        "Day-HR",
        *columns,
    ])

    gt_obj = (
        GT(display_df)
        .tab_style(
            style=style.fill("white"),
            locations=loc.body(columns=columns),
        )
        .fmt_number(
            columns=columns,
            decimals=0,
        )
    )

    for column in columns:
        for val, color in color_map.items():
            gt_obj = gt_obj.tab_style(
                style=[
                    style.fill(color),
                    style.text(color="#1f2937"),
                ],
                locations=loc.body(
                    columns=column, 
                    rows=pl.col(column).cast(
                        pl.Int64,
                        strict=False,
                    ) == val,
                ),
            )

    return gt_obj

def _build_matrix_group(description, direction, df, HOUR_LABELS):
    """
    Building the matrix into lane closure logic and weekdays and weekends.
    """
    # day_names = ["Weekday", "SAT", "SUN"]
    # weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    # weekends = day_names[1:]

    HOUR_IDS = [
        f"{'-'.join(format_hour(x, idx) for idx, x in enumerate(label.split(' to ')))}" 
        for label in HOUR_LABELS
    ]
    if "ROAD_NAME" in df.columns and "GAZETTAL_DIRECTION" in df.columns:
        filtered = df.filter((pl.col("DESCRIPTION") == description) & (pl.col("GAZETTAL_DIRECTION") == direction)).clone()
        if filtered.is_empty():
            rows = []
            for day_name in day_names:
                record = {"Direction": direction, "Day-HR": day_name}
                for hour in HOUR_IDS:
                    record[hour] = 1
                rows.append(record)
            return pl.DataFrame(rows)
        rows = []
        for day in day_names:
            if "HOUR" in filtered.columns:
                filtered = filtered.select('HOUR', pl.exclude('HOUR'))

            target_cols = [day] if day in weekends else weekdays
            values = filtered.with_columns(
                pl.concat_list(target_cols).alias("DAYNAMES")
            )
            values = values.with_columns(pl.col("DAYNAMES").map_elements(lane_closure_logic))
            # values = filtered.loc[:, [day] if day in weekends else weekdays].apply(lane_closure_logic, axis=1)

            record = {"Direction": direction, "Day-HR": day}
            for hour_id, label in zip(HOUR_IDS, HOUR_LABELS):
                # if label in values:
                if label in values['HOUR']:
                    # Simple heuristic NEED integration with road inventory to identify the road type.
                    vol_df = values.filter(pl.col("HOUR") == label).select("DAYNAMES").mean()
                    print(f"DF = {vol_df}")
                    vol_item = (vol_df.item())
                    lanes = int(vol_item // 1000) + 1 if vol_item else 0
                    record[hour_id] = lanes if lanes else 0
                else:
                    record[hour_id] = 0
            rows.append(record)
        temp = pl.DataFrame(rows)
        return temp
    temp = pl.DataFrame({"Direction": direction, "Day-HR": ["Weekday", "Saturday", "Sunday"]})
    return temp

def _style_matrix(frame: pl.DataFrame) -> Styler:
    """
    Edifying the matrix-like table to be looking similar to General Access Times.
    """
    hour_columns = [col for col in frame.columns if col not in {"Direction", "Day-HR"}]
    def color_value(value):
        v = _safe_int(value)
        if v is None:
            return "background-color: white; color: #1f2937;"
        color = COLOR_MAP.get(v, "#ffffff")
        return f"background-color: {color}; color: #1f2937; font-weight: bold;"

    styled = frame.style.map(color_value, subset=hour_columns)
    styled = styled.format("{:.0f}", subset=hour_columns, na_rep="")
    styled = styled.set_properties(**{"border": "1px solid #dfe3e8", "text-align": "center", "padding": "8px"})
    styled = styled.set_table_styles([
        {"selector": "th", "props": [("background-color", "#1f3f5f"), ("color", "white"), ("font-weight", "bold"), ("padding", "8px"), ("text-align", "center")]},
        {"selector": "td", "props": [("border", "1px solid #edf2f7"), ("padding", "8px"), ("text-align", "center")]},
    ])
    return styled

def display_matrix(frame: pl.DataFrame) -> None:
    hour_columns = ['12-1am', '1-2am', '2-3am', '3-4am', '4-5am', '5-6am', '6-7am', '7-8am', '8-9am', '9-10am', '10-11am', '11-12pm', '12-1pm', '1-2pm', '2-3pm', '3-4pm', '4-5pm', '5-6pm', '6-7pm', '7-8pm', '8-9pm', '9-10pm', '10-11pm', '11-12am']

    frame = frame.with_columns(
        [
            pl.col(col)
            .cast(pl.Float64, strict=False)
            .alias(col)
            for col in hour_columns
        ]
    )
    column_config = {"Direction": st.column_config.TextColumn("Direction"), "Day-HR": st.column_config.TextColumn("Day-HR")}
    for col in hour_columns:
        column_config[col] = st.column_config.NumberColumn(
            col,
            format="%.0f",
        )

    styled = apply_value_coloring(frame, hour_columns, COLOR_MAP)
    return styled, column_config

def _display_hour_label(hour_label):
    return "-".join(
        format_hour(value, index)
        for index, value in enumerate(hour_label.split(" to "))
    )

def _get_cell_traceability(df, street_name, description, direction, day_name, display_hour):
    """Return the source values and calculation used for one displayed matrix cell."""
    matching_rows = df.filter(
        (pl.col("ROAD_NAME") == street_name)
        & (pl.col("DESCRIPTION") == description)
        & (pl.col("GAZETTAL_DIRECTION") == direction)
    )
    if matching_rows.is_empty():
        return {
            "source": "No matching source rows; the matrix fallback value is used.",
            "input_values": [],
            "percentile_85": None,
            "lane_value": 1,
        }

    raw_hour = next(
        (
            hour
            for hour in matching_rows["HOUR"].unique().to_list()
            if _display_hour_label(hour) == display_hour
        ),
        None,
    )
    if raw_hour is None:
        return {
            "source": "No source row exists for this hour.",
            "input_values": [],
            "percentile_85": None,
            "lane_value": 0,
        }

    hour_rows = matching_rows.filter(pl.col("HOUR") == raw_hour)
    target_columns = [day_name] if day_name in weekends else weekdays
    available_columns = [column for column in target_columns if column in hour_rows.columns]
    if not available_columns:
        return {
            "source": "The source data does not contain the required day columns.",
            "input_values": [],
            "percentile_85": None,
            "lane_value": None,
        }

    input_values = [
        value
        for column in available_columns
        for value in hour_rows[column].to_list()
        if value is not None
    ]
    if not input_values:
        return {
            "source": "The source rows contain no values for this day and hour.",
            "input_values": [],
            "percentile_85": None,
            "lane_value": 0,
        }

    percentile_85 = lane_closure_logic(pl.Series(input_values))
    lane_value = int(percentile_85 // 1000) + 1 if percentile_85 else 0
    return {
        "source": "Workbook traffic values",
        "input_values": input_values,
        "percentile_85": percentile_85,
        "lane_value": lane_value,
    }

def _selected_cell_from_event(event):
    cells = event.selection.cells
    if not cells:
        return None
    row_index, column_name = cells[0]
    return int(row_index), column_name

def _render_cell_traceability(trace):
    with st.sidebar:
        st.subheader("Details")
        st.write(f"**Road:** {trace['street']}")
        st.write(f"**Description:** {trace['description']}")
        st.write(f"**Direction:** {trace['direction']}")
        st.write(f"**Day type:** {trace['day_name']}")
        st.write(f"**Hour:** {trace['hour']}")
        st.write(f"**Displayed lanes:** {trace['display_value']}")

        if trace["percentile_85"] is None:
            st.write("**Calculation:** No percentile calculation was available.")
        else:
            st.write(f"**Input traffic values:** {trace['input_values']}")
            st.write(f"**85th percentile:** {trace['percentile_85']}")
            if trace["percentile_85"]:
                formula = f"int({trace['percentile_85']} // 1000) + 1"
            else:
                formula = "0 (the 85th percentile is zero)"
            st.write(f"**Lane calculation:** {formula} = {trace['lane_value']}")

def render_matrix():
    """
    Render matrix-like table for visualizing the number of lanes to be opened (or closed).
    """
    # df = _load_matrix_df()
    if "raw_data" not in st.session_state:
        df = _load_matrix_df
    else:
        df = st.session_state.raw_data
    if df.is_empty():
        st.warning("No matrix data was available to render.")
        return

    street_names = sorted(set(df["ROAD_NAME"].drop_nulls().to_list())) if "ROAD_NAME" in df.columns else ["Aster Road"]
    direction_values = sorted(set(df["GAZETTAL_DIRECTION"].drop_nulls().to_list())) if "GAZETTAL_DIRECTION" in df.columns else ["WB", "EB"]
    HOUR_LABELS = df['HOUR'].unique()
    if not street_names:
        street_names = ["Aster Road"]
    if not direction_values:
        direction_values = ["WB", "EB"]

    # # search_term = st.text_input("Search by Road Name:", "")
    # # tt = df.filter(pl.col("ROAD_NAME").str.contains(search_term))
    # print(tt.head())
    total_pages = len(street_names)

    page = st.number_input(
        "Page number",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1
    )

    selected_street = street_names[page - 1]
    st.title("Road Closure Table View")
    st.subheader(f"{selected_street} access hours by direction and day type")

    if st.button("Download PDF"):
        pdf_buffer = export_df_to_pdf(df)  # Use raw df, not styled_df
        st.download_button(
            label="Click to Download",
            data=pdf_buffer,
            file_name="table_no_style.pdf",
            mime="application/pdf"
        )

    filtered_df = df.filter(pl.col("ROAD_NAME") == selected_street)
    descs = sorted(set(filtered_df["DESCRIPTION"].drop_nulls().to_list()))
    selected_trace = None

    for street_desc in descs:
        matrix = pl.DataFrame()
        left_matrix = _build_matrix_group(street_desc, direction_values[0], filtered_df, HOUR_LABELS)
        right_matrix = _build_matrix_group(street_desc, direction_values[1] if len(direction_values) > 1 else direction_values[0], filtered_df, HOUR_LABELS)

        matrix = pl.concat([left_matrix, right_matrix])
        st.markdown(f"#### {selected_street} - {street_desc}")
        hour_columns = [column for column in matrix.columns if column not in {"Direction", "Day-HR"}]
        display_df = matrix.to_pandas()

        def color_value(value):
            number = _safe_int(value)
            color = COLOR_MAP.get(number, "#ffffff")
            return f"background-color: {color}; color: #1f2937; font-weight: bold;"

        styled_df = display_df.style.map(color_value, subset=hour_columns).format(
            "{:.0f}", subset=hour_columns, na_rep=""
        )
        event = st.dataframe(
            styled_df,
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-cell",
            key=f"matrix-{selected_street}-{street_desc}",
        )
        selected_cell = _selected_cell_from_event(event)
        if selected_cell is not None:
            row_index, column_name = selected_cell
            if column_name in hour_columns and 0 <= row_index < matrix.height:
                row = matrix.row(row_index, named=True)
                direction = row["Direction"]
                day_name = row["Day-HR"]
                details = _get_cell_traceability(
                    filtered_df,
                    selected_street,
                    street_desc,
                    direction,
                    day_name,
                    column_name,
                )
                selected_trace = {
                    "street": selected_street,
                    "description": street_desc,
                    "direction": direction,
                    "day_name": day_name,
                    "hour": column_name,
                    "display_value": row[column_name],
                    **details,
                }

        st.info(LEGEND_TEXT)
        st.divider()

    if selected_trace is not None:
        _render_cell_traceability(selected_trace)
    else:
        with st.sidebar:
            st.subheader("Cell computation details")
            st.caption("Select a lane-value cell in the table to view its source values and calculation.")
