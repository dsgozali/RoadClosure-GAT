from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse

from .common import page_context
from ..constants import COLOR_MAP, LEGEND_TEXT
from ..services import build_matrix, get_cell_traceability


def matrix(request):
    context = page_context(request)
    roads = context["roads"]
    selected_road = request.GET.get("road", "")
    # if ":" in selected_road:
    #     selected_road = selected_road.split(": ")[1]
    selected_view = request.GET.get("show-volume", "off")
    # selected_view = (request.GET.get("show-volume") == "1")
    if selected_road not in roads and roads:
        selected_road = roads[-1]
    print(f"SELECTED = {selected_road}")
    matrices = build_matrix(context["frame"], selected_road, selected_view) if selected_road else []
    for matrix_data in matrices:
        matrix_data["display_rows"] = []
        for row in matrix_data["rows"]:
            cells = []
            for hour in matrix_data["columns"][2:]:
                value = row.get(hour, "")
                query = urlencode(
                    {
                        "region": context["region"],
                        "road": selected_road,
                        "description": matrix_data["description"],
                        "direction": row["Direction"],
                        "day": row["Day-HR"],
                        "hour": hour,
                    }
                ) if value != "" else ""
                cells.append(
                    {
                        "value": value,
                        "hour": hour,
                        "url": f"{reverse('racp:matrix')}?{query}" if query else "",
                        "color": COLOR_MAP.get(row.get(hour), "#ffffff"),
                    }
                )
            matrix_data["display_rows"].append({**row, "cells": cells})

    selected_trace = None
    selection = {
        key: request.GET.get(key, "")
        for key in ("description", "direction", "day", "hour")
    }
    if all(selection.values()) and selected_road:
        details = get_cell_traceability(
            context["frame"],
            selected_road,
            selection["description"],
            selection["direction"],
            selection["day"],
            selection["hour"],
        )
        matrix_data = next(
            (item for item in matrices if item["description"] == selection["description"]),
            None,
        )
        selected_row = next(
            (
                row
                for row in matrix_data["rows"]
                if row["Direction"] == selection["direction"]
                and row["Day-HR"] == selection["day"]
            ),
            {},
        ) if matrix_data else {}
        selected_trace = {
            "road": selected_road,
            "display_value": selected_row.get(selection["hour"], details["lane_value"]),
            **selection,
            **details,
        }

    context.update(
        {
            "matrices": matrices,
            "selected_road": selected_road,
            "selected_trace": selected_trace,
            "color_map": COLOR_MAP,
            "legend_text": LEGEND_TEXT,
            "matrix_url": reverse("racp:matrix"),
        }
    )
    return render(request, "racp/matrix.html", context)
