import typing
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db import models
from django.utils.functional import cached_property
from strawberry.dataloader import DataLoader

from .models import (
    Admin1,
    Alert,
    AlertAdmin1,
    AlertInfo,
    AlertInfoArea,
    AlertInfoAreaCircle,
    AlertInfoAreaGeocode,
    AlertInfoAreaPolygon,
    AlertInfoParameter,
    Continent,
    Country,
    Feed,
    LanguageInfo,
    Region,
)

if typing.TYPE_CHECKING:
    from .types import (
        Admin1Type,
        AlertInfoAreaCircleType,
        AlertInfoAreaGeocodeType,
        AlertInfoAreaPolygonType,
        AlertInfoAreaType,
        AlertInfoParameterType,
        AlertInfoType,
        ContinentType,
        CountryType,
        FeedType,
        LanguageInfoType,
        RegionType,
    )


def _load_model(Model: models.Model, keys: list[int]):
    qs = Model.objects.filter(id__in=keys)
    _map = {obj.pk: obj for obj in qs}
    return [_map[key] for key in keys]


def load_country(keys: list[int]) -> list["CountryType"]:
    return _load_model(Country, keys)  # type: ignore[reportGeneralTypeIssues]


def load_region(keys: list[int]) -> list["RegionType"]:
    return _load_model(Region, keys)  # type: ignore[reportGeneralTypeIssues]


def load_continent(keys: list[int]) -> list["ContinentType"]:
    return _load_model(Continent, keys)  # type: ignore[reportGeneralTypeIssues]


def load_feed(keys: list[int]) -> list["FeedType"]:
    return _load_model(Feed, keys)  # type: ignore[reportGeneralTypeIssues]


def load_admin1_by_alert(keys: list[int]) -> list[list["Admin1Type"]]:
    qs = (
        AlertAdmin1.objects.filter(alert__in=keys)
        .order_by()
        .values("admin1")
        .annotate(alert_ids=ArrayAgg("alert_id", distinct=True))
    )

    _map = defaultdict(list)
    relation_map = {admin1_id: alert_ids for admin1_id, alert_ids in qs.values_list("admin1", "alert_ids")}
    admin1_map = {admin1.pk: admin1 for admin1 in Admin1.objects.filter(pk__in=qs.values("admin1"))}

    for admin1_id, alert_ids in relation_map.items():
        for alert_id in alert_ids:
            _map[alert_id].append(admin1_map[admin1_id])

    return [_map[key] for key in keys]


def load_admin1s_by_country(keys: list[int]) -> list[list["Admin1Type"]]:
    qs = Admin1.objects.filter(country__in=keys)
    _map = defaultdict(list)
    for admin1 in qs.all():
        _map[admin1.country_id].append(admin1)
    return [_map[key] for key in keys]


def load_info_by_alert(keys: list[int]) -> list[typing.Union["AlertInfoType", None]]:
    qs = (
        AlertInfo.objects.filter(alert__in=keys)
        # TODO: Is this order good enough?
        .order_by("alert_id", "id")
        .distinct("alert_id")
        .all()
    )

    _map: dict[int, "AlertInfoType"] = {  # type: ignore[reportGeneralTypeIssues]
        alert_info.alert_id: alert_info for alert_info in qs
    }

    return [_map.get(key) for key in keys]


def load_infos_by_alert(keys: list[int]) -> list[list["AlertInfoType"]]:
    qs = AlertInfo.objects.filter(alert__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.alert_id].append(obj)

    return [_map[key] for key in keys]


def load_info_parameters_by_info(keys: list[int]) -> list[list["AlertInfoParameterType"]]:
    qs = AlertInfoParameter.objects.filter(alert_info__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.alert_info_id].append(obj)

    return [_map[key] for key in keys]


def load_info_areas_by_info(keys: list[int]) -> list[list["AlertInfoAreaType"]]:
    qs = AlertInfoArea.objects.filter(alert_info__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.alert_info_id].append(obj)

    return [_map[key] for key in keys]


def load_info_area_polygons_by_info_area(keys: list[int]) -> list[list["AlertInfoAreaPolygonType"]]:
    qs = AlertInfoAreaPolygon.objects.filter(alert_info_area__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.alert_info_area_id].append(obj)

    return [_map[key] for key in keys]


def load_info_area_circles_by_info_area(keys: list[int]) -> list[list["AlertInfoAreaCircleType"]]:
    qs = AlertInfoAreaCircle.objects.filter(alert_info_area__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.alert_info_area_id].append(obj)

    return [_map[key] for key in keys]


def load_info_area_geocodes_by_info_area(keys: list[int]) -> list[list["AlertInfoAreaGeocodeType"]]:
    qs = AlertInfoAreaGeocode.objects.filter(alert_info_area__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.alert_info_area_id].append(obj)

    return [_map[key] for key in keys]


def load_language_info_by_feed(keys: list[int]) -> list[list["LanguageInfoType"]]:
    qs = LanguageInfo.objects.filter(feed_id__in=keys).all()

    _map = defaultdict(list)
    for obj in qs:
        _map[obj.feed_id].append(obj)

    return [_map[key] for key in keys]


def load_alert_count_by_country(keys: list[int]) -> list[int]:
    qs = (
        Alert.get_queryset()
        .filter(country__in=keys)
        .order_by()
        .values("country_id")
        .annotate(
            count=models.Count("id"),
        )
        .values_list("country_id", "count")
    )

    _map = {country_id: count for country_id, count in qs}

    return [_map.get(key, 0) for key in keys]


def load_alert_count_by_admin1(keys: list[int]) -> list[int]:
    qs = (
        Alert.get_queryset()
        .filter(admin1s__in=keys)
        .order_by()
        .values("admin1s")
        .annotate(
            count=models.Count("id"),
        )
        .values_list("admin1s", "count")
    )

    _map = {admin1_id: count for admin1_id, count in qs}

    return [_map.get(key, 0) for key in keys]


class CapFeedDataloader:

    @cached_property
    def load_country(self):
        return DataLoader(load_fn=sync_to_async(load_country))

    @cached_property
    def load_region(self):
        return DataLoader(load_fn=sync_to_async(load_region))

    @cached_property
    def load_continent(self):
        return DataLoader(load_fn=sync_to_async(load_continent))

    @cached_property
    def load_feed(self):
        return DataLoader(load_fn=sync_to_async(load_feed))

    @cached_property
    def load_admin1s_by_alert(self):
        return DataLoader(load_fn=sync_to_async(load_admin1_by_alert))

    @cached_property
    def load_admin1s_by_country(self):
        return DataLoader(load_fn=sync_to_async(load_admin1s_by_country))

    @cached_property
    def load_info_by_alert(self):
        return DataLoader(load_fn=sync_to_async(load_info_by_alert))

    @cached_property
    def load_infos_by_alert(self):
        return DataLoader(load_fn=sync_to_async(load_infos_by_alert))

    @cached_property
    def load_info_parameters_by_info(self):
        return DataLoader(load_fn=sync_to_async(load_info_parameters_by_info))

    @cached_property
    def load_info_areas_by_info(self):
        return DataLoader(load_fn=sync_to_async(load_info_areas_by_info))

    @cached_property
    def load_info_area_polygons_by_info_area(self):
        return DataLoader(load_fn=sync_to_async(load_info_area_polygons_by_info_area))

    @cached_property
    def load_info_area_circles_by_info_area(self):
        return DataLoader(load_fn=sync_to_async(load_info_area_circles_by_info_area))

    @cached_property
    def load_info_area_geocodes_by_info_area(self):
        return DataLoader(load_fn=sync_to_async(load_info_area_geocodes_by_info_area))

    @cached_property
    def load_language_info_by_feed(self):
        return DataLoader(load_fn=sync_to_async(load_language_info_by_feed))

    @cached_property
    def load_alert_count_by_country(self):
        return DataLoader(load_fn=sync_to_async(load_alert_count_by_country))

    @cached_property
    def load_alert_count_by_admin1(self):
        return DataLoader(load_fn=sync_to_async(load_alert_count_by_admin1))
