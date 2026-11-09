"""
General Access Reports Detail Queries

Returns the raw source rows that back each summary dashboard card.
"""

from racp.models import FactTaTrafficVolumeReport15Min

qs = FactTaTrafficVolumeReport15Min.objects.select_related("site_id", "traffic_class_id")[:5]

print(qs.query)

for r in qs:
    print(r.site_id, r.traffic_class_id, r.sum_volume)