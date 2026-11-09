from django.http import HttpResponse
from django.shortcuts import render

from .common import page_context
from ..services import (
    build_matrix,
    build_matrix2,
    create_matrix_pdf,
    dataframe_to_pdf,
    get_road_data,
    get_road_names,
)


def pdf_view(request):
    context = page_context(request)
    selected_road = request.GET.get("road", "")
    show_vol = request.GET.get("show-export-volume", "")
    if selected_road not in context["roads"] and context["roads"]:
        selected_road = context["roads"][0]
    matrices = build_matrix(context["frame"], selected_road, show_vol) if selected_road else []
    # matrices = build_matrix2(context["frame"])
    context.update({"selected_road": selected_road, "matrices": matrices})
    return render(request, "racp/analytics.html", context)

def pdf_download(request):
    context = page_context(request)
    selected_road = request.GET.get("road", "")
    roadall = request.GET.get("roadall", "")
    show_vol = request.GET.get("show-export-volume", "")
    print(f"SHOW = {show_vol}")
    if selected_road not in context["roads"]:
        selected_road = ""
    frame = get_road_data(context["frame"], context["region"] or None)
    roads = [selected_road] if selected_road else get_road_names(frame)
    matrices = [matrix_data for road in roads for matrix_data in build_matrix(frame, road, show_vol)]
    if selected_road:
        pdf = create_matrix_pdf(matrices, selected_road or None)
    elif roadall:
        pdf = dataframe_to_pdf(matrices, roadall or None)
    response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="road-closure-matrix.pdf"'
    return response
