import dash_mantine_components as dmc
from dash import dcc, dash_table

from utils.consts import COLOR_MAP
from utils.miscs import label_id_generator

def get_graph(index: str) -> dmc.Skeleton:
    return dmc.Skeleton(
        id={"type": "skeleton", "index": index},
        visible=True,
        children=dmc.AspectRatio(
            dcc.Graph(id={"type": "graph", "index": index}, responsive=True),
            ratio=1.618034,
        ),
        mb=10,
    )

def get_matrix(matrices) -> None:
    labels, ids = label_id_generator()
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