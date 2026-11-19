from ..services import get_regions, get_road_data, get_road_names, load_traffic_data, load_road_geometries


def page_context(request, road=None, region=None):
    frame = load_traffic_data(road=road, region=region)
    region = request.GET.get("region", "").strip()
    regions = get_regions(frame)
    if region not in regions:
        region = ""
    selected_data = get_road_data(frame, region or None)
    roads = [x.split(": ")[1] for x in get_road_names(selected_data)]
    roads = load_road_geometries(tuple(roads))
    return {
        "frame": frame,
        "region": region,
        "regions": regions,
        "roads": get_road_names(selected_data),
        "roads_geo": roads
    }
