from typing import Dict, List
from io import BytesIO
from fpdf import FPDF

from utils.consts import hour_to_pm, EXTERNAL_API, COLOR_MAP
from utils.apis import fetch_local_data, fetch_remote_data, lane_closure_logic

def format_hour(x_str, idx):
    x = int(x_str)
    res = x_str
    if 0 < x < 13:
        res = x_str if idx == 0 else f"{x_str}am"
    elif x == 0:
        res = '12' if idx == 0 else "12pm"
    else:
        res = str(hour_to_pm[x]) if idx == 0 else f"{hour_to_pm[x]}pm"
    return res

def label_id_generator(val_df):
    HOUR_LABELS = []
    if 'HOUR' in val_df:
        HOUR_LABELS = val_df['HOUR'].unique()

    HOUR_IDS = [
        f"hour_{'_'.join(format_hour(x, idx) for idx, x in enumerate(label.split(' to ')))}" 
        for label in HOUR_LABELS
    ]

    return HOUR_IDS, HOUR_LABELS

def build_matrix_rows(street: str, direction: str) -> List[Dict[str, object]]:
    if EXTERNAL_API:
        _, values_df = fetch_remote_data()
    else:
        _, values_df = fetch_local_data()

    ids, labels = label_id_generator(values_df)
    day_names = ["Weekday", "SAT", "SUN"]
    weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    weekends = day_names[1:]
    rows: List[Dict[str, object]] = []

    for day in day_names:
        row: Dict[str, object] = {
            "Direction": direction,
            "Day-HR": day,
        }
        temp_values = values_df.loc[(values_df['ROAD_NAME'] == street) & (values_df['GAZETTAL_DIRECTION'] == direction)].set_index('HOUR')      
        values = temp_values.loc[:, [day] if day in weekends else weekdays].apply(lane_closure_logic, axis=1)
        for hour_id, label in zip(ids, labels):
            if label in values:
                row[hour_id] = round(values.loc[label], 2)
        rows.append(row)

    return rows

def build_data_table(matrices):
    if EXTERNAL_API:
        _, values_df = fetch_remote_data()
    else:
        _, values_df = fetch_local_data()
    ids, labels = label_id_generator(values_df)
    matrix = {'street': matrices[0]['street'], 'rows': matrices[0]['rows'] + matrices[1]['rows']}
    columns = [
        {"name": "Direction", "id": "Direction"},
        {"name": "Day-HR", "id": "Day-HR"},
    ] + [{"name": label, "id": hour_id} for label, hour_id in zip(labels, ids)]
    
    style_data_conditional = []

    for hour_id in ids:
        for value, color in COLOR_MAP.items():
            style_data_conditional.append(
                {
                    "if": {"column_id": hour_id, "filter_query": f"{{{hour_id}}} = {value}"},
                    "backgroundColor": color,
                    "color": "#1f2937",
                    "fontWeight": "bold",
                }
            )

    return dash_table.DataTable(
        id={"type": "matrix-table", "street": matrix["street"]},
        columns=columns,
        data=matrix["rows"],
        style_table={
            "overflowX": "auto",
            "minWidth": "900px",
            "border": "1px solid #dfe3e8",
            "borderRadius": "10px",
            "backgroundColor": "#fff",
        },
        style_header={
            "backgroundColor": "#1f3f5f",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": "8px",
            "border": "1px solid #dfe3e8",
        },
        style_cell={
            "padding": "8px",
            "textAlign": "center",
            "fontSize": "12px",
            "border": "1px solid #edf2f7",
            "minWidth": "60px",
            "maxWidth": "90px",
            "whiteSpace": "nowrap",
        },
        style_data_conditional=style_data_conditional,
        page_action="none",
        sort_action="native",
        fill_width=False,
    )

def matrices_generator():
    if EXTERNAL_API:
        header_df, _ = fetch_remote_data()
    else:
        header_df, _ = fetch_local_data()
    
    Street_mat = [
        {
            "street": row['ROAD_NAME'],
            "direction": row['GAZETTAL_DIRECTION']
        }
        for _, row in header_df.iterrows()
    ]

    return [
        {
            "street": item["street"],
            "direction": item["direction"],
            "rows": build_matrix_rows(item["street"], item["direction"]),
        }
        for item in Street_mat
    ]

def export_df_to_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    col_width = pdf.w / (len(dataframe.columns) + 1)
    pdf.cell(col_width, 10, "Index", border=1)
    for col in dataframe.columns:
        pdf.cell(col_width, 10, col, border=1)
    pdf.ln()

    for idx, row in dataframe.iterrows():
        pdf.cell(col_width, 10, str(idx), border=1)
        for val in row:
            pdf.cell(col_width, 10, str(val), border=1)
        pdf.ln()

    pdf_bytes = pdf.output()
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer