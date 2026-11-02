from ..services import get_regions, get_road_data, get_road_names, load_traffic_data


def page_context(request):
    frame = load_traffic_data()
    region = request.GET.get("region", "").strip()
    regions = get_regions(frame)
    if region not in regions:
        region = ""
    selected_data = get_road_data(frame, region or None)
    return {
        "frame": frame,
        "region": region,
        "regions": regions,
        "roads": get_road_names(selected_data),
    }
