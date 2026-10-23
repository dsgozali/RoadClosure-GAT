# import pandas as pd
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_pdf import PdfPages

# df = pd.DataFrame({
#    "Name": ["Alice", "Bob", "Charlie"],
#    "Age": [25, 30, 35],
#    "City": ["New York", "Los Angeles", "Chicago"]
# })

# def render_pdf():
#     fig, ax = plt.subplots(figsize=(8, 4))
#     ax.axis('tight')
#     ax.axis('off')
#     table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
#     pdf = PdfPages("output.pdf")
#     pdf.savefig(fig, bbox_inches='tight')
#     pdf.close()

import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

from utils.apis import _load_matrix_df
from utils.consts import LEGEND_TEXT
from pages.matrix import _build_matrix_group, _style_matrix

def pl_to_mat(df):
    street_names = sorted(set(df["ROAD_NAME"].dropna().tolist())) if "ROAD_NAME" in df.columns else ["Aster Road"]
    direction_values = sorted(set(df["GAZETTAL_DIRECTION"].dropna().tolist())) if "GAZETTAL_DIRECTION" in df.columns else ["WB", "EB"]

    descs = sorted(set(df["DESCRIPTION"].dropna().tolist()))
    
    for street_name in street_names:
        matrix = pd.DataFrame()
        left_matrix = _build_matrix_group(street_name, direction_values[0], df)
        right_matrix = _build_matrix_group(street_name, direction_values[1] if len(direction_values) > 1 else direction_values[0], df)

        matrix = pd.concat([left_matrix, right_matrix], ignore_index=True)
        st.markdown(f"#### {street_name}")
        st.dataframe(_style_matrix(matrix), width="stretch", hide_index=True)

        st.info(LEGEND_TEXT)
        st.divider()
    
    

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
    df = _load_matrix_df()

    # Display DataFrame
    st.dataframe(df)

    # Button to export PDF
    if st.button("Export to PDF"):
        pdf_buffer = dataframe_to_pdf(df)
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="dataframe_export.pdf",
            mime="application/pdf"
        )



