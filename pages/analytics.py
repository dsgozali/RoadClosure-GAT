import streamlit as st
import polars as pl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

from utils.apis import _load_matrix_df
from pages.matrix import _build_matrix_group, display_matrix

# def build_street_group(street_name, direction, df, HOUR_LABELS):
#     """
#     Building the matrix into lane closure logic and weekdays and weekends.
#     """
#     day_names = ["Weekday", "SAT", "SUN"]
#     weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI']
#     weekends = day_names[1:]

#     HOUR_IDS = [
#         f"{'-'.join(format_hour(x, idx) for idx, x in enumerate(label.split(' to ')))}" 
#         for label in HOUR_LABELS
#     ]
#     if "ROAD_NAME" in df.columns and "GAZETTAL_DIRECTION" in df.columns:
#         filtered = df.filter((pl.col("ROAD_NAME") == street_name) & (pl.col("GAZETTAL_DIRECTION") == direction)).clone()
#         if filtered.is_empty():
#             rows = []
#             for day_name in day_names:
#                 record = {"Direction": direction, "Day-HR": day_name}
#                 for hour in HOUR_IDS:
#                     record[hour] = 1
#                 rows.append(record)
#             return pl.DataFrame(rows)
#         rows = []
#         unique_descs = filtered["DESCRIPTION"].unique().to_list()

#             temp_f = filtered.filter(pl.col("DESCRIPTION") == desc)
#             for day in day_names:
#                 if "HOUR" in filtered.columns:
#                     temp_f = temp_f.select('HOUR', pl.exclude('HOUR'))

#                 target_cols = [day] if day in weekends else weekdays
#                 values = temp_f.with_columns(
#                     pl.concat_list(target_cols).alias("DAYNAMES")
#                 )
#                 values = values.with_columns(pl.col("DAYNAMES").map_elements(lane_closure_logic))
#                 # values = filtered.loc[:, [day] if day in weekends else weekdays].apply(lane_closure_logic, axis=1)

#                 record = {"Direction": direction, "Day-HR": day}
#                 for hour_id, label in zip(HOUR_IDS, HOUR_LABELS):
#                     # if label in values:
#                     if label in values['HOUR']:
#                         # Simple heuristic NEED integration with road inventory to identify the road type.
#                         vol_item = (values.filter(pl.col("HOUR") == label).select("DAYNAMES").item())
#                         lanes = int(vol_item // 1000) + 1 if vol_item else 0
#                         record[hour_id] = lanes if lanes else 0
#                     else:
#                         record[hour_id] = 0
#             rows.append(record)
#         temp = pl.DataFrame(rows)
#         return temp
#     temp = pl.DataFrame({"Direction": direction, "Day-HR": ["Weekday", "Saturday", "Sunday"]})
#     return temp

@st.cache_data
def pl_to_mat(df):
    street_names = sorted(set(df["ROAD_NAME"].drop_nulls().to_list())) if "ROAD_NAME" in df.columns else ["Aster Road"]
    direction_values = sorted(set(df["GAZETTAL_DIRECTION"].drop_nulls().to_list())) if "GAZETTAL_DIRECTION" in df.columns else ["WB", "EB"]
    HOUR_LABELS = df['HOUR'].unique()

    mat_dfs = pl.DataFrame()
    i = 0
    for street_name in street_names:
        filtered_df = df.filter(pl.col("ROAD_NAME") == street_name)
        unique_descs = filtered_df["DESCRIPTION"].unique().to_list()
        for desc in unique_descs:
            left_matrix = _build_matrix_group(desc, direction_values[0], filtered_df, HOUR_LABELS)
            right_matrix = _build_matrix_group(desc, direction_values[1] if len(direction_values) > 1 else direction_values[0], filtered_df, HOUR_LABELS)

            matrix = pl.concat([left_matrix, right_matrix])
            styled, column_config = display_matrix(matrix)
            html_table = styled.as_raw_html(inline_css=True, all_important=True)

            if i < 10:
                st.markdown(f"#### {street_name} - {desc}")
                st.markdown(html_table, unsafe_allow_html=True)
            
            mat_dfs = pl.concat([mat_dfs, matrix])
            i+=1

    return mat_dfs

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
        c.drawString(50 + dataframe.columns.get_loc(col) * 150, y, str(col))

    # Table rows
    c.setFont("Helvetica", 12)
    for idx, row in dataframe.iterrows():
        y -= 20
        for col in dataframe.columns:
            c.drawString(50 + dataframe.columns.get_loc(col) * 150, y, str(row[col]))

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def render_pdf():
    st.title("Exportable PDF View")
    # df = _load_matrix_df()
    if "raw_data" not in st.session_state:
        df = _load_matrix_df
    else:
        df = st.session_state.raw_data

    mat_dfs = pl_to_mat(df)

    # Button to export PDF
    if st.button("Export to PDF"):
        pdf_buffer = dataframe_to_pdf(mat_dfs)
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="dataframe_export.pdf",
            mime="application/pdf"
        )

    # # Display DataFrame
    # st.dataframe(df)



