import json
from django.urls import reverse
from django.shortcuts import render

from .common import page_context
from ..services import build_map_points, load_road_geometries


def home(request):
    context = page_context(request)
    selected_road = request.GET.get("road", "")
    region = request.GET.get("region", "")
    points = build_map_points(context["frame"], context["region"] or None)
    roads_json = context["roads_geo"].to_json()
    print(f"pts = {points}")
    selected_matrix = None
    if selected_road:
        selected_matrix = {
            "road": selected_road,
            "region": region
        }
    context.update(
        {
            "map_points": points,
            "map_points_json": json.dumps(points),
            "road_count": len(points),
            "roads_json": roads_json,
            "selected_matrix": selected_matrix,
            "matrix_url": reverse("racp:matrix")
        }
    )
    return render(request, "racp/home.html", context)
