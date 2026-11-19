import json
from django.shortcuts import render
from django.urls import reverse
from urllib.parse import urlencode

from .common import page_context
from ..services import build_matrix2
from ..constants import static_road, static_region, COLOR_MAP


def test(request):
    context = page_context(request, road=static_road, region=static_region)
    # context['frame'].write_csv("gympie-sample.csv")
    selected_road = static_road.upper()
    print(f"CONText FRAME = {context['frame']}")
    filters = build_matrix2(context["frame"], selected_road) if selected_road else ""
    
    print(f"before loop after build_matrix matrices = {filters}")
    print(f"dicts ONTEXT = {context['frame'].to_pandas().to_dict('records')}")
    context.update(
        {
            "rows": context['frame'].to_pandas().to_dict("records"),
            "filters": filters,
            "selected_road": selected_road,
            "selected_trace": "",
            "color_map": COLOR_MAP,
            "legend_text": "This is a Test",
            "matrix_url": reverse("racp:test"),
        }
    )
    return render(request, "racp/test.html", context)
