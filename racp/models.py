# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db.models import (
    Case,
    CharField,
    F,
    Sum,
    Avg,
    Value,
    When
)
from django.db.models.functions import ExtractHour, ExtractWeekDay, ExtractIsoWeekDay
# class TaPoints(models.Model):
#     point_id = models.BigIntegerField(blank=True, null=False, primary_key=True, db_comment='Unique id of the point. The physical point on the road network where the site is located.')
#     dist_id = models.BigIntegerField(blank=True, null=True, db_comment='The district that defines the actual location of the site.  This is a redundant column, as the location of the counter is defined by the Point ID column, and further, this column is being removed as part of regionalisation.')
#     rsect_id = models.TextField(blank=True, null=True, db_comment='Road section id. (#supposed)')
#     rstatus_id = models.TextField(blank=True, null=True, db_comment='ROAD status id. (#supposed)')
#     link_id = models.BigIntegerField(blank=True, null=True, db_comment='Link Id. (#supposed)')
#     tdist = models.FloatField(blank=True, null=True, db_comment='Starting point of a road segment in terms of distance from a defined reference point (District)')
#     # u_date = models.DateField(blank=True, null=True, db_comment='Date when the data was last updated or captured.')
#     point_inter_id = models.BigIntegerField(blank=True, null=True, db_comment='(#supposed)')
#     description = models.TextField(blank=True, null=True, db_comment='Point description.')
#     # is_deleted_record = models.BooleanField(blank=True, null=True, db_comment='Indicates whether the record has been deleted in the source system.')
#     # is_current_record = models.BooleanField(blank=True, null=True, db_comment='Identifies if the record represents the most current version of the data.')
#     # audit_source_hash = models.TextField(blank=True, null=True, db_comment='TDC audit column. Hash value generated on source payload record.')
#     # audit_source_blob = models.TextField(blank=True, null=True, db_comment='TDC audit column. Source file S3 path.')
#     # audit_source_row_id = models.TextField(blank=True, null=True, db_comment='TDC audit column. The index of the element, if it is an array in the source file; otherwise NULL.')
#     # audit_record_sequence = models.BigIntegerField(blank=True, null=True, db_comment='TDC audit column. Row number over unique key in the source file.')
#     # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
#     # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
#     # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.
#     # audit_flg_migrated_record = models.BooleanField(blank=True, null=True, db_comment='TDC audit column. Flag if record was migrated from legacy system.')
#     latitude = models.FloatField(blank=True, null=True)
#     longitude = models.FloatField(blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'TA_POINTS'


class TaPoints(models.Model):
    point_id = models.BigIntegerField(blank=True, null=False, primary_key=True, db_comment='Unique id of the point. The physical point on the road network where the site is located.')
    dist_id = models.BigIntegerField(blank=True, null=True, db_comment='The district that defines the actual location of the site.  This is a redundant column, as the location of the counter is defined by the Point ID column, and further, this column is being removed as part of regionalisation.')
    rsect_id = models.TextField(blank=True, null=True, db_comment='Road section id. (#supposed)')
    rstatus_id = models.TextField(blank=True, null=True, db_comment='ROAD status id. (#supposed)')
    # link_id = models.ForeignKey(TaSite)
    link_id = models.BigIntegerField(blank=True, null=True, db_comment='Link Id. (#supposed)')
    tdist = models.FloatField(blank=True, null=True, db_comment='Starting point of a road segment in terms of distance from a defined reference point (District)')
    u_date = models.DateField(blank=True, null=True, db_comment='Date when the data was last updated or captured.')
    point_inter_id = models.BigIntegerField(blank=True, null=True, db_comment='(#supposed)')
    description = models.TextField(blank=True, null=True, db_comment='Point description.')
    # is_deleted_record = models.BooleanField(blank=True, null=True, db_comment='Indicates whether the record has been deleted in the source system.')
    # is_current_record = models.BooleanField(blank=True, null=True, db_comment='Identifies if the record represents the most current version of the data.')
    # audit_source_hash = models.TextField(blank=True, null=True, db_comment='TDC audit column. Hash value generated on source payload record.')
    # audit_source_blob = models.TextField(blank=True, null=True, db_comment='TDC audit column. Source file S3 path.')
    # audit_source_row_id = models.TextField(blank=True, null=True, db_comment='TDC audit column. The index of the element, if it is an array in the source file; otherwise NULL.')
    # audit_record_sequence = models.BigIntegerField(blank=True, null=True, db_comment='TDC audit column. Row number over unique key in the source file.')
    # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
    # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
    # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.
    # audit_flg_migrated_record = models.BooleanField(blank=True, null=True, db_comment='TDC audit column. Flag if record was migrated from legacy system.')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TA_POINTS'

class TaSite(models.Model):
    site_id = models.BigIntegerField(blank=True, null=False, primary_key=True, db_comment='Site Id in the Site table. Unique identifier from sequence ta_site_number.  Sequence starts at dist_id*10000.')
    # dist_id = models.BigIntegerField(blank=True, null=True, db_comment='The district that defines the actual location of the site.  This is a redundant column, as the location of the counter is defined by the Point ID column, and further, this column is being removed as part of regionalisation.')
    site_type = models.TextField(blank=True, null=True, db_comment='Intersections are handled by Coverage sites only.  Road segments can be handled by Permanent of Coverage sites.')
    description = models.TextField(blank=True, null=True, db_comment='Generally a description of the location of the counter, eg, �Stevens Street at Gold Coast Hwy�')
    # u_date = models.TextField(blank=True, null=True, db_comment='Last updated date.')  # This field type is a guess.
    # speed_limit = models.BigIntegerField(blank=True, null=True, db_comment='Speed limit for the intersection or collection segment.')
    inter_id = models.BigIntegerField(blank=True, null=True, db_comment='INTER : Intersection id in Road Reference')
    # inter_leg_num = models.BigIntegerField(blank=True, null=True, db_comment='INTER : The leg number on the intersection where the counter is placed.')
    # leg_angle = models.BigIntegerField(blank=True, null=True, db_comment='INTER : The angle from North for leg 1 (most northerly leg) to help align the intersection diagram.')
    # point_id = models.BigIntegerField(blank=True, null=True, db_comment='The physical point on the road network where the site is located.')
    point_id = models.ForeignKey(TaPoints, models.DO_NOTHING, db_column='point_id', blank=True, null=True, db_comment='The physical point on the road network where the site is located.')
    anticipated_growth = models.BigIntegerField(blank=True, null=True, db_comment='Rarely used, and then only on coverage sites.')
    # rebuild_segs = models.TextField(blank=True, null=True, db_comment='Flag to indicate whether the segment rebuild process should include this site.  This was added to assist performance of the overnight rebuild process.')
    # is_deleted_record = models.BooleanField(blank=True, null=True, db_comment='Indicates whether the record has been deleted in the source system.')
    # is_current_record = models.BooleanField(blank=True, null=True, db_comment='Identifies if the record represents the most current version of the data.')
    # audit_source_hash = models.TextField(blank=True, null=True, db_comment='TDC audit column. Hash value generated on source payload record.')
    # audit_source_blob = models.TextField(blank=True, null=True, db_comment='TDC audit column. Source file S3 path.')
    # audit_source_row_id = models.TextField(blank=True, null=True, db_comment='TDC audit column. The index of the element, if it is an array in the source file; otherwise NULL.')
    # audit_record_sequence = models.BigIntegerField(blank=True, null=True, db_comment='TDC audit column. Row number over unique key in the source file.')
    # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
    # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
    # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.
    # audit_flg_migrated_record = models.BooleanField(blank=True, null=True, db_comment='TDC audit column. Flag if record was migrated from legacy system.')

    class Meta:
        managed = False
        db_table = 'TA_SITE'


class TaSitePoints(models.Model):
    # point_id = models.ForeignKey(TaPoints, models.DO_NOTHING, db_column='point_id', blank=True, null=True, db_comment='Site Id in the Site table. Unique identifier from sequence ta_site_number.  Sequence starts at dist_id*10000.')
    site_id = models.ForeignKey(TaSite, models.DO_NOTHING, primary_key=True, unique=True, db_column='site_id', db_comment='Site Id in the Site table. Unique identifier from sequence ta_site_number.  Sequence starts at dist_id*10000.')
    # site_id = models.BigIntegerField(blank=True, null=True, db_comment='Site Id in the Site table. Unique identifier from sequence ta_site_number.  Sequence starts at dist_id*10000.')
    start_traffic_year = models.BigIntegerField(blank=True, null=True, db_comment='Traffic Year (YYYY) when point definition of the site is started to be actual. (#supposed)')
    # start_point = models.BigIntegerField(blank=True, null=True, db_comment='Point id where road site starts. (#supposed)')
    # end_point = models.BigIntegerField(blank=True, null=True, db_comment='Point id where road site ends. (#supposed)')
    start_point = models.ForeignKey(TaPoints, models.DO_NOTHING, null=True, blank=True, db_column='start_point', related_name='ta_site_points_start_point_set', db_comment='Point id where road site starts. (#supposed)')
    end_point = models.ForeignKey(TaPoints, models.DO_NOTHING, null=True, blank=True, db_column='end_point', related_name='ta_site_points_end_point_set', db_comment='Point id where road site ends. (#supposed)')
    dist_id = models.BigIntegerField(blank=True, null=True, db_comment='The district that defines the actual location of the site.  This is a redundant column, as the location of the counter is defined by the Point ID column, and further, this column is being removed as part of regionalisation.')
    end_traffic_year = models.BigIntegerField(blank=True, null=True, db_comment='Traffic Year (YYYY) when point definition of the site is ended to be actual. (#supposed)')
    u_date = models.TextField(blank=True, null=True, db_comment='Date when the data was last updated or captured.')  # This field type is a guess.
    # is_deleted_record = models.BooleanField(blank=True, null=True, db_comment='Indicates whether the record has been deleted in the source system.')
    # is_current_record = models.BooleanField(blank=True, null=True, db_comment='Identifies if the record represents the most current version of the data.')
    # audit_source_hash = models.TextField(blank=True, null=True, db_comment='TDC audit column. Hash value generated on source payload record.')
    # audit_source_blob = models.TextField(blank=True, null=True, db_comment='TDC audit column. Source file S3 path.')
    # audit_source_row_id = models.TextField(blank=True, null=True, db_comment='TDC audit column. The index of the element, if it is an array in the source file; otherwise NULL.')
    # audit_record_sequence = models.BigIntegerField(blank=True, null=True, db_comment='TDC audit column. Row number over unique key in the source file.')
    # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
    # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
    # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.
    # audit_flg_migrated_record = models.BooleanField(blank=True, null=True, db_comment='TDC audit column. Flag if record was migrated from legacy system.')

    class Meta:
        managed = False
        db_table = 'TA_SITE_POINTS'

class DimTaRoadSectionPoint(models.Model):
    sk_ta_road_section_point = models.BigIntegerField(primary_key=True, db_comment='Unique surrogate key of the record.')
    ta_road_section_point_id = models.BigIntegerField(blank=True, null=True, db_comment='Source id of the Point on a road network.')
    ta_district_id = models.BigIntegerField(blank=True, null=True, db_comment='The district that defines the actual location of the site. This is a redundant column due to regionalisation.')
    rsect_id = models.TextField(blank=True, null=True, db_comment='Road section id. (#supposed)')
    rstatus_id = models.TextField(blank=True, null=True, db_comment='ROAD status id. (#supposed)')
    link_id = models.BigIntegerField(blank=True, null=True, db_comment='Link Id. (#supposed)')
    tdist = models.FloatField(blank=True, null=True, db_comment='Starting point of a road segment in terms of distance from a defined reference point (District)')
    point_inter_id = models.BigIntegerField(blank=True, null=True, db_comment='(#supposed)')
    description = models.TextField(blank=True, null=True, db_comment='Point description.')
    road_section_point_geography = models.TextField(blank=True, null=True, db_comment='Geo coordinates of the point on the road network.')  # This field type is a guess.
    # is_deleted_record = models.BooleanField(blank=True, null=True, db_comment='Indicates whether the record has been logically deleted.')
    # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
    # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
    # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'DIM_TA_ROAD_SECTION_POINT'

class DimTaRoadSite(models.Model):
    sk_ta_road_site = models.BigIntegerField(primary_key=True, db_comment='Unique surrogate key of the record.')
    ta_road_site_id = models.BigIntegerField(blank=True, null=True, db_comment='Source id of the road Site.')
    # sk_ta_road_site_perm_sstr = models.ForeignKey(DimTaRoadSite, models.DO_NOTHING, db_column='sk_ta_road_site_perm_sstr', blank=True, null=True, db_comment='Foreign key. Referring DIM_TA_ROAD_SITE.')
    sk_ta_road_site_perm_sstr = models.BigIntegerField(blank=True, null=True, db_comment='Foreign key. Referring DIM_TA_ROAD_SITE.')
    # sk_ta_traffic_stream_perm_sstr = models.ForeignKey('DimTaTrafficStream', models.DO_NOTHING, db_column='sk_ta_traffic_stream_perm_sstr', blank=True, null=True, db_comment='Foreign key. Referring DIM_TA_TRAFFIC_STREAM.')
    # sk_ta_road_section_point_site_location = models.ForeignKey('DimTaRoadSectionPoint', models.DO_NOTHING, db_column='sk_ta_road_section_point_site_location', blank=True, null=True, db_comment='Foreign key. The physical point on the road network where the site is located. Referring DIM_TA_ROAD_SECTION_POINT.')
    sk_ta_road_section_point_site_location = models.ForeignKey(DimTaRoadSectionPoint, models.DO_NOTHING, db_column='sk_ta_road_section_point_site_location', blank=True, null=True, db_comment="The physical point on the road network where the site is located. Referring DIM_TA_ROAD_SECTION_POINT.")
    sk_ta_road_section_point_start = models.ForeignKey(DimTaRoadSectionPoint, models.DO_NOTHING, db_column='sk_ta_road_section_point_start', related_name='dimtaroadsite_sk_ta_road_section_point_start_set', blank=True, null=True, db_comment="Foreign key. The physical point where collection Site starts.(#supposed) Referring DIM_TA_ROAD_SECTION_POINT.")
    sk_ta_road_section_point_end = models.ForeignKey(DimTaRoadSectionPoint, models.DO_NOTHING, db_column='sk_ta_road_section_point_end', related_name='dimtaroadsite_sk_ta_road_section_point_end_set', blank=True, null=True, db_comment="Foreign key. The physical point where collection Site ends.(#supposed) Referring DIM_TA_ROAD_SECTION_POINT.")
    # sk_ta_road_section_point_start = models.ForeignKey('DimTaRoadSectionPoint', models.DO_NOTHING, db_column='sk_ta_road_section_point_start', related_name='dimtaroadsite_sk_ta_road_section_point_start_set', blank=True, null=True, db_comment='Foreign key. The physical point where collection Site starts.(#supposed) Referring DIM_TA_ROAD_SECTION_POINT.')
    # sk_ta_road_section_point_end = models.ForeignKey('DimTaRoadSectionPoint', models.DO_NOTHING, db_column='sk_ta_road_section_point_end', related_name='dimtaroadsite_sk_ta_road_section_point_end_set', blank=True, null=True, db_comment='Foreign key. The physical point where collection Site ends.(#supposed) Referring DIM_TA_ROAD_SECTION_POINT.')
    ta_district_id = models.BigIntegerField(blank=True, null=True, db_comment='The district that defines the actual location of the site. This is a redundant column due to regionalisation.')
    description = models.TextField(blank=True, null=True, db_comment='Generally a description of the location of the counter, eg, �Stevens Street at Gold Coast Hwy�')
    # speed_limit = models.FloatField(blank=True, null=True, db_comment='Speed limit for the intersection or collection segment.')
    ta_road_intersection_id = models.BigIntegerField(blank=True, null=True, db_comment='INTER : Intersection id in Road Reference')
    # ta_road_intersection_leg_num = models.BigIntegerField(blank=True, null=True, db_comment='INTER : The leg number on the intersection where the counter is placed.')
    # ta_road_intersection_leg_angle = models.BigIntegerField(blank=True, null=True, db_comment='INTER : The angle from North for leg 1 (most northerly leg) to help align the intersection diagram.')
    # anticipated_growth = models.BigIntegerField(blank=True, null=True, db_comment='Anticipated growth. Rarely used, and then only on coverage sites.')
    # flg_site_in_segments_rebuild = models.BooleanField(blank=True, null=True, db_comment='Flag to indicate whether the segment rebuild process should include this site.  This was added to assist performance of the overnight rebuild process.')
    # year_traffic_start = models.BigIntegerField(blank=True, null=True, db_comment='Traffic Year (YYYY) when point definition of the site is started to be actual. (#supposed)')
    # year_traffic_end = models.BigIntegerField(blank=True, null=True, db_comment='Traffic Year (YYYY) when point definition of the site is ended to be actual. (#supposed)')
    # is_deleted_record = models.BooleanField(blank=True, null=True, db_comment='Indicates whether the record has been logically deleted.')
    # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
    # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
    # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'DIM_TA_ROAD_SITE'

class FactTaTrafficVolumeReport15Min(models.Model):
    skf_ta_traffic_volume_report_15_min = models.BigIntegerField(primary_key=True, db_comment='Unique surrogate key of the record.')
    # sk_ta_road_site = models.ForeignKey('DimTaRoadSite', models.DO_NOTHING, db_column='sk_ta_road_site', blank=True, null=True, db_comment='Foreign key. Collection road Site. Referring DIM_TA_ROAD_SITE.')
    ta_road_site_id = models.BigIntegerField(blank=True, null=True, db_comment='Source id of the road Site.')
    code_t_gazettal_direction = models.TextField(blank=True, null=True, db_comment='Gazettal direction of the site stream (flow of traffic at a road Site): G - gazettla, A - anti-gazettal, B - both')
    # time_start_15_min_window_aest = models.TextField(blank=True, null=True, db_comment='Start of the 15 minute window of volume aggregation.')  # This field type is a guess.
    time_start_15_min_window_aest = models.DateTimeField(blank=True, null=True, db_comment="Start of the 15 min window of volume agg.")
    date_traffic_volume = models.DateField(blank=True, null=True, db_comment='Traffic date.')
    sum_volume = models.BigIntegerField(blank=True, null=True, db_comment='Sum of traffic volumes of all vehicle types on a site within 15 minutes.')
    ta_traffic_class_hierarchy = models.TextField(blank=True, null=True, db_comment='Traffic class bin based on classification: 12, 4, 2, All vehicles.')
    code_ta_traffic_class = models.TextField(blank=True, null=True, db_comment='Code of the traffic class.')
    sk_ta_traffic_class = models.BigIntegerField(blank=True, null=True, db_comment="Traffic class")
    # # sk_ta_traffic_class = models.ForeignKey('DimTaTrafficClass', models.DO_NOTHING, db_column='sk_ta_traffic_class', blank=True, null=True, db_comment='Foreign key. Traffic class. Referring DIM_TA_TRAFFIC_CLASS.')
    # audit_create_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Effective timestamp from the source payload record.')  # This field type is a guess.
    # audit_insert_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually inserted.')  # This field type is a guess.
    # audit_update_timestamp = models.TextField(blank=True, null=True, db_comment='TDC audit column. Technical timestamp when record was actually updated.')  # This field type is a guess.
    flg_is_full_day = models.TextField(blank=True, null=True, db_comment='Is data captured for the complete day')
    status = models.TextField(blank=True, null=True, db_comment='P or U')
    class Meta:
        managed = False
        db_table = 'FACT_TA_TRAFFIC_VOLUME_REPORT_15_MIN'

def get_DIM_static(road_section_id):
    # segpoint = DimTaRoadSectionPoint.objcts.values("sk_ta_road_section_point", "road_section_point_geography")
    # segstart = DimTaRoadSectionPoint.objects.values("sk_ta_road_section_point", "road_section_point_geography")
    # segend = DimTaRoadSectionPoint.objects.values("sk_ta_road_section_point", "road_section_point_geography")
    dim_stat = DimTaRoadSite.objects.select_related(
        "ta_road_site_id", 
        "sk_ta_road_section_point_site_location",
        "sk_ta_road_section_point_start",
        "sk_ta_road_section_point_end"
    ).filter(
        sk_ta_road_section_point_site_location__rsect_id=road_section_id
    ).values(
        "ta_road_site_id", 
        "sk_ta_road_section_point_site_location",
        "sk_ta_road_section_point_start",
        "sk_ta_road_section_point_end"
    )

    return dim_stat

def get_TA_volume_road(sites, year=2025):
    """
    Returns all TA that recorded in the given year
    """
    try:
        year = int(year)
    except Exception as e:
        print("MUST BE AN INTEGER")
    print(f"UNIQUE VOL SITES = {sites}")

    objects = FactTaTrafficVolumeReport15Min.objects.select_related("ta_road_site_id").filter(ta_road_site_id__in=sites).values() \
        .filter(
            time_start_15_min_window_aest__gte=f"{year}-01-01", 
            time_start_15_min_window_aest__lt=f"{year+1}-01-01" # maximum traffic year!
        ) \
        .annotate(
            hour=ExtractHour("time_start_15_min_window_aest"),
            weekday_num=ExtractIsoWeekDay("time_start_15_min_window_aest")
        ) \
        .filter(
            code_t_gazettal_direction__in=['TA', 'TG'],
            code_ta_traffic_class = '00'
        ) \
        .annotate(
            day_type=Case(
                When(weekday_num=1, then=Value("SUN")),
                When(weekday_num=2, then=Value("MON")),
                When(weekday_num=3, then=Value("TUE")),
                When(weekday_num=4, then=Value("WED")),
                When(weekday_num=5, then=Value("THU")),
                When(weekday_num=6, then=Value("FRI")),
                When(weekday_num=7, then=Value("SAT")),
                default=Value("WEEKDAY"),
                output_field=CharField(),
            )
        ) \
        .values(
            "ta_road_site_id",
            "code_t_gazettal_direction",
            "code_ta_traffic_class",
            "sk_ta_traffic_class",
            "hour",
            "weekday_num",
            "day_type",
            "sum_volume",
        ) \
        .order_by(
            "ta_road_site_id",
            "hour",
        )
    return objects


def get_TA_volume(sites, year=2025):
    """
    Returns all TA that recorded in the given year
    """
    try:
        year = int(year)
    except Exception as e:
        print("MUST BE AN INTEGER")
    print(f"UNIQUE VOL SITES = {sites}")

    objects = FactTaTrafficVolumeReport15Min.objects.select_related("ta_road_site_id").filter(ta_road_site_id__in=sites).values() \
        .filter(
            time_start_15_min_window_aest__gte=f"{year}-01-01", 
            time_start_15_min_window_aest__lt=f"{year+1}-01-01" # maximum traffic year!
        ) \
        .annotate(
            hour=ExtractHour("time_start_15_min_window_aest"),
            weekday_num=ExtractIsoWeekDay("time_start_15_min_window_aest")
        ) \
        .filter(
            code_t_gazettal_direction__in=['TA', 'TG'],
            code_ta_traffic_class = '00'
        ) \
        .annotate(
            day_type=Case(
                When(weekday_num=1, then=Value("SUN")),
                When(weekday_num=2, then=Value("MON")),
                When(weekday_num=3, then=Value("TUE")),
                When(weekday_num=4, then=Value("WED")),
                When(weekday_num=5, then=Value("THU")),
                When(weekday_num=6, then=Value("FRI")),
                When(weekday_num=7, then=Value("SAT")),
                default=Value("WEEKDAY"),
                output_field=CharField(),
            )
        ) \
        .values(
            "ta_road_site_id",
            "code_t_gazettal_direction",
            "code_ta_traffic_class",
            "sk_ta_traffic_class",
            "hour",
            "weekday_num",
            "day_type",
        ) \
        .annotate(
            total_vol=Avg("sum_volume"),
        ) \
        .order_by(
            "ta_road_site_id",
            "hour",
            "day_type"
        )

    return objects


# import polars as pl
# fetch_data = 
# (   
# FactTaTrafficVolumeReport15Min.objects.filter(date_traffic_volume__year = 2025).values("ta_road_site_id").annotate(total_vol=sum("SUM_VOLUME")).order_by("ta_road_site_id")
# )
# temp = pl.DataFrame(list(fetch_data)) 


# FactTaTrafficVolumeReport15Min.objects \
#     .filter(
#         time_start_15_min_window_aest__gte="2025-01-01", 
#         time_start_15_min_window_aest__lt="2026-01-01"
#     ) \
#     .annotate(
#         hour=ExtractHour("time_start_15_min_window_aest"),
#         weekday_num=ExtractIsoWeekDay("time_start_15_min_window_aest")
#     ) \
#     .filter(
#         code_t_gazettal_direction__in=['TA', 'TG'],
#         code_ta_traffic_class = '00'
#     ) \
#     .annotate(
#         day_type=
#             Case(
#                 When(weekday_num=1, then=Value("SUN")),
#                 When(weekday_num=7, then=Value("SAT")),
#                 default=Value("WEEKDAY"),
#                 output_field=CharField(),
#             )
#     ) \
#     .values(
#         "ta_road_site_id",
#         "code_t_gazettal_direction",
#         "sum_volume",
#         "code_ta_traffic_class",
#         "sk_ta_traffic_class",
#         "hour",
#         "weekday_num",
#         "day_type"
#     ) \
#     .annotate(
#         total_vol=Sum("sum_volume"),
#     ) \
#     .order_by(
#         "ta_road_site_id",
#         "hour",
#         "day_type"
#     )
