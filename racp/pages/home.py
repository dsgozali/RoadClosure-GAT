import json

from django.shortcuts import render

from .common import page_context
from ..services import build_map_points


def home(request):
    context = page_context(request)
    points = build_map_points(context["frame"], context["region"] or None)
    print(f"points = {context}")
    context.update(
        {
            "map_points": points,
            "map_points_json": json.dumps(points),
            "road_count": len(points),
        }
    )
    return render(request, "racp/home.html", context)
