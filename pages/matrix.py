# import pandas as pd
import polars as pl
import streamlit as st
from pandas.io.formats.style import Styler
from great_tables import style, loc, GT


from utils.consts import COLOR_MAP, LEGEND_TEXT, HOUR_LABELS, hour_to_pm
from utils.miscs import format_hour, export_df_to_pdf
from utils.apis import lane_closure_logic, _load_matrix_df

def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def apply_value_coloring(df, columns, color_map):
    """Applies dynamic cell backgrounds and text styles based on cell values."""
    # Handle the 'None' / missing value default fallback styling
    gt_obj = (
        GT(df)
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
            try:
                v = int(val)  # Safe integer conversion equivalent
            except (ValueError, TypeError):
                continue

            gt_obj = gt_obj.tab_style(
                style=[
                    style.fill(color),
                    style.text(color="#1f2937", weight="bold"),
                ],
                # Target cells where the value matches 'v'
                locations=loc.body(columns=column, rows=pl.col(column).cast(
                        pl.Int64,
                        strict=False,
                    ) == v,
                ),
            )

    return gt_obj

def _build_matrix_group(description, direction, df, HOUR_LABELS):
    """
    Building the matrix into lane closure logic and weekdays and weekends.
    """
    day_names = ["Weekday", "SAT", "SUN"]
    weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    weekends = day_names[1:]

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
                    # lanes = (values.loc[label] // 1000) + 1
                    lanes = ((values.filter(pl.col("HOUR") == label).select("DAYNAMES").item()) // 1000) + 1
                    record[hour_id] = lanes if lanes else 0
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
    id_columns = {"Direction", "Day-HR"}

    hour_columns = [
        col
        for col in frame.columns
        if col not in id_columns
    ]

    # Ensure hour columns are numeric
    frame = frame.with_columns(
        [
            pl.col(col)
            .cast(pl.Float64, strict=False)
            .alias(col)
            for col in hour_columns
        ]
    )

    # Streamlit column configuration
    column_config = {
        "Direction": st.column_config.TextColumn(
            "Direction"
        ),
        "Day-HR": st.column_config.TextColumn(
            "Day-HR"
        ),
    }

    # Configure all hour columns to display 0 decimal places
    for col in hour_columns:
        column_config[col] = st.column_config.NumberColumn(
            col,
            format="%.0f",
        )

    styled = apply_value_coloring(frame, hour_columns, COLOR_MAP)
    return styled, column_config


def render_matrix():
    """
    Render matrix-like table for visualizing the number of lanes to be opened (or closed).
    """
    df = _load_matrix_df()
    print(df.shape)
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

    if st.button("Download PDF (No Styling)"):
        pdf_buffer = export_df_to_pdf(df)  # Use raw df, not styled_df
        st.download_button(
            label="Click to Download",
            data=pdf_buffer,
            file_name="table_no_style.pdf",
            mime="application/pdf"
        )

    filtered_df = df.filter(pl.col("ROAD_NAME") == selected_street)
    descs = sorted(set(filtered_df["DESCRIPTION"].drop_nulls().to_list()))

    for street_desc in descs:
        # matrix = pd.DataFrame()
        matrix = pl.DataFrame()
        left_matrix = _build_matrix_group(street_desc, direction_values[0], filtered_df, HOUR_LABELS)
        right_matrix = _build_matrix_group(street_desc, direction_values[1] if len(direction_values) > 1 else direction_values[0], filtered_df, HOUR_LABELS)

        matrix = pl.concat([left_matrix, right_matrix])
        st.markdown(f"#### {selected_street} - {street_desc}")
        # st.dataframe(_style_matrix(matrix), width="stretch", hide_index=True)

        styled, column_config = display_matrix(matrix)
        html_table = styled.as_raw_html(inline_css=True, all_important=True)

        # Display in Streamlit
        st.markdown(html_table, unsafe_allow_html=True)
        # st.dataframe(
        #     frame,
        #     column_config=column_config,
        #     hide_index=True,
        #     width='stretch',
        # )

        st.info(LEGEND_TEXT)
        st.divider()

   
    # # Number of items per page
    # items_per_page = 2

    # page_number = st.pagination(
    #     num_pages=(len(street_names) - 1) // items_per_page + 1,
    #     default=1
    # )
    # # Calculate start and end indices
    # start_idx = (page_number - 1) * items_per_page
    # end_idx = start_idx + items_per_page

    # # Display paginated data
    # st.write(f"Showing page {page_number}")
    # # st.dataframe(data.iloc[start_idx:end_idx])

    # for street_name in street_names:
        
    #     matrix = pd.DataFrame()
    #     left_matrix = _build_matrix_group(street_name, direction_values[0], df)
    #     right_matrix = _build_matrix_group(street_name, direction_values[1] if len(direction_values) > 1 else direction_values[0], df)

    #     matrix = pd.concat([left_matrix, right_matrix], ignore_index=True)
    #     st.markdown(f"#### {street_name}")
    #     st.dataframe(_style_matrix(matrix), width="stretch", hide_index=True)

    #     st.info(LEGEND_TEXT)
    #     st.divider()

