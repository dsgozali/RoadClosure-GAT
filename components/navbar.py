import dash
import dash_mantine_components as dmc
from dash import html


def load_navbar() -> dmc.AppShellNavbar:
    return dmc.AppShellNavbar(
        id="navbar",
        children=[
            html.Div(
                children=[
                    dmc.NavLink(label=page["name"], href=page["path"], active="exact")
                    for page in dash.page_registry.values()
                ]
            ),
        ],
        p="md",
    )
