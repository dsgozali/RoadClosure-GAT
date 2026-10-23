import plotly.graph_objects as go
import plotly.io as pio
from dash import (
    ALL,
    Input,
    Output,
    Patch,
    State,
    callback,
    no_update,
)

import utils.apis as api
import utils.consts as consts

@callback(
    Output('geojson', 'data'),
    Input('dropdown', 'value')
)
def update_map(selected_value):
    if selected_value == 'opt1':
        return {"type": "FeatureCollection", "features": []} # Add your GeoJSON data here
    else:
        return {"type": "FeatureCollection", "features": []} # Add your GeoJSON data here

@callback(
    Output({"type": "graph", "index": ALL}, "figure", allow_duplicate=True),
    Input("color-scheme-toggle", "checked"),
    State({"type": "graph", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def update_graph_theme(dark_mode: bool, ids: list[str]) -> list[go.Figure]:
    template = (
        pio.templates[consts.DARK_THEME]
        if dark_mode
        else pio.templates[consts.LIGHT_THEME]
    )
    figs = []
    for _ in ids:
        fig = Patch()
        fig.layout.template = template
        figs.append(fig)
    return figs
