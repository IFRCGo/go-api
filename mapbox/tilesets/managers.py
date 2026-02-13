import pathlib
import subprocess

import typing_extensions
from django.core.management.base import BaseCommand
from django.utils.functional import cached_property

from .base import MapboxConfig, RecipeConfig, TilesetMetadata, TilesetsManagerBase


class CountryTilesetsManager(TilesetsManagerBase):
    name = "Go Countries"

    recipe_config = RecipeConfig(
        minzoom=0,
        maxzoom=10,
    )

    @cached_property
    def metadata(self):
        if self.mapbox_config.is_prod:
            return TilesetMetadata(
                tileset_id="go-countries",
                tileset_source_id="go-countries-src",
            )
        return TilesetMetadata(
            tileset_id="go-countries-staging",
            tileset_source_id="go-countries-src-staging",
        )

    def _sql_for_tileset_source(self):
        return (
            pathlib.Path("/tmp/countries.geojson"),
            """
            SELECT
                cd.country_id,
                cd.geom,
                c.name,
                c.name_es,
                c.name_fr,
                c.name_ar,
                c.iso,
                c.region_id,
                c.iso3,
                c.independent,
                c.is_deprecated,
                c.disputed,
                c.fdrs,
                c.record_type
            FROM
                api_countrygeoms cd,
                api_country c
            WHERE
                cd.country_id = c.id
                AND c.record_type=1
        """,
        )

    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        subprocess.check_call(
            [
                "ogr2ogr",
                "-f",
                "GeoJSON",
                str(temp_source_data_file),
                self.db_helper.connection_string,
                "-sql",
                source_data_sql,
            ]
        )


class CountryCentroidsTilesetsManager(TilesetsManagerBase):
    name = "Go Countries Centroids"

    recipe_config = RecipeConfig(
        minzoom=0,
        maxzoom=10,
    )

    @cached_property
    def metadata(self):
        if self.mapbox_config.is_prod:
            return TilesetMetadata(
                tileset_id="go-country-centroids",
                tileset_source_id="go-country-centroids",
            )
        return TilesetMetadata(
            tileset_id="go-country-centroids-staging",
            tileset_source_id="go-country-centroids-staging",
        )

    def _sql_for_tileset_source(self):
        return (
            pathlib.Path("/tmp/country-centroids.geojson"),
            """
            SELECT
                id as country_id,
                name_en as name,
                name_ar,
                name_es,
                name_fr,
                independent,
                disputed,
                is_deprecated,
                iso,
                iso3,
                record_type,
                fdrs,
                region_id,
                centroid
            FROM api_country
            WHERE
                centroid is not null
        """,
        )

    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        subprocess.check_call(
            [
                "ogr2ogr",
                "-lco",
                "COORDINATE_PRECISION=4",
                "-f",
                "GeoJSON",
                str(temp_source_data_file),
                self.db_helper.connection_string,
                "-sql",
                source_data_sql,
            ]
        )


class DistrictTilesetsManager(TilesetsManagerBase):
    name = "Go Districts"

    recipe_config = RecipeConfig(
        minzoom=3,
        maxzoom=10,
    )

    @cached_property
    def metadata(self):
        if self.mapbox_config.is_prod:
            return TilesetMetadata(
                tileset_id="go-districts-1",
                tileset_source_id="go-districts-src-1",
            )
        return TilesetMetadata(
            tileset_id="go-districts-staging",
            tileset_source_id="go-districts-src-staging",
        )

    def _sql_for_tileset_source(self):
        # FIXME eventually should be name_en, name_es etc. (NOTE: fixme from existing codebase)
        return (
            pathlib.Path("/tmp/districts.geojson"),
            """
            SELECT
                cd.district_id,
                cd.geom,
                c.name,
                c.code,
                c.country_id,
                c.is_enclave,
                c.is_deprecated,
                country.iso as country_iso,
                country.iso3 as country_iso3,
                country.name as country_name,
                country.name_es as country_name_es,
                country.name_fr as country_name_fr,
                country.name_ar as country_name_ar
            FROM
                api_districtgeoms cd,
                api_district c,
                api_country country
            WHERE
                cd.district_id = c.id
                AND cd.geom is not null
                AND country.id=c.country_id
        """,
        )

    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        subprocess.check_call(
            [
                "ogr2ogr",
                "-lco",
                "COORDINATE_PRECISION=5",
                "-f",
                "GeoJSON",
                str(temp_source_data_file),
                self.db_helper.connection_string,
                "-sql",
                source_data_sql,
            ]
        )


class DistrictCentroidsTilesetsManager(TilesetsManagerBase):
    name = "Go Districts Centroids"

    recipe_config = RecipeConfig(
        minzoom=3,
        maxzoom=10,
    )

    @cached_property
    def metadata(self):
        if self.mapbox_config.is_prod:
            return TilesetMetadata(
                tileset_id="go-district-centroids",
                tileset_source_id="go-district-centroids",
            )
        return TilesetMetadata(
            tileset_id="go-district-centroids-staging",
            tileset_source_id="go-district-centroids-staging",
        )

    def _sql_for_tileset_source(self):
        # FIXME eventually should be name_en, name_es etc. (NOTE: fixme from existing codebase)
        return (
            pathlib.Path("/tmp/district-centroids.geojson"),
            """
            SELECT
                d.id as district_id,
                d.country_id as country_id,
                d.name,
                d.code,
                d.is_deprecated,
                d.is_enclave,
                c.iso as country_iso,
                c.iso3 as country_iso3,
                c.name as country_name,
                c.name_es as country_name_es,
                c.name_fr as country_name_fr,
                c.name_ar as country_name_ar,
                d.centroid
            FROM
                api_district d
                JOIN api_country c on d.country_id=c.id
            WHERE d.centroid is not null
        """,
        )

    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        subprocess.check_call(
            [
                "ogr2ogr",
                "-lco",
                "COORDINATE_PRECISION=4",
                "-f",
                "GeoJSON",
                str(temp_source_data_file),
                self.db_helper.connection_string,
                "-sql",
                source_data_sql,
            ]
        )


class Admin2ManagerBase(TilesetsManagerBase):

    @typing_extensions.override
    def __init__(
        self,
        *,
        command: BaseCommand,
        mapbox_config: MapboxConfig,
        iso3: str,
    ):
        self.iso3 = iso3
        self.name = f"{self.name} - {iso3}"
        super().__init__(command=command, mapbox_config=mapbox_config)


class Admin2TilesetsManager(Admin2ManagerBase):
    name = "Go Admin2s"

    recipe_config = RecipeConfig(
        minzoom=5,
        maxzoom=10,
    )

    @cached_property
    def metadata(self):
        if self.mapbox_config.is_prod:
            return TilesetMetadata(
                tileset_id=f"go-admin2-{self.iso3}",
                tileset_source_id=f"go-admin2-{self.iso3}-src",
            )
        return TilesetMetadata(
            tileset_id=f"go-admin2-{self.iso3}-staging",
            tileset_source_id=f"go-admin2-{self.iso3}-src-staging",
        )

    def _sql_for_tileset_source(self):
        # FIXME eventually should be name_en, name_es etc. (NOTE: fixme from existing codebase)
        return (
            pathlib.Path(f"/tmp/{self.iso3}.geojson"),
            f"""
            SELECT
                d.id as admin1_id,
                d.name as admin1_name,
                ad.name,
                ad.id,
                ad.code,
                adg.geom
            FROM api_country as c,
                api_district as d,
                api_admin2 as ad,
                api_admin2geoms as adg
            WHERE
                c.id=d.country_id
                AND c.iso3='{self.iso3}'
                AND ad.admin1_id=d.id
                AND adg.admin2_id = ad.id
        """,
        )

    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        subprocess.check_call(
            [
                "ogr2ogr",
                "-f",
                "GeoJSON",
                str(temp_source_data_file),
                self.db_helper.connection_string,
                "-sql",
                source_data_sql,
            ]
        )


class Admin2CentroidsTilesetsManager(Admin2ManagerBase):
    name = "Go Admin2s Centroids"

    recipe_config = RecipeConfig(
        minzoom=3,
        maxzoom=10,
    )

    @cached_property
    def metadata(self):
        if self.mapbox_config.is_prod:
            return TilesetMetadata(
                tileset_id=f"go-admin2-{self.iso3}-centroids",
                tileset_source_id=f"go-admin2-{self.iso3}-centroids-src",
            )
        return TilesetMetadata(
            tileset_id=f"go-admin2-{self.iso3}-centroids-staging",
            tileset_source_id=f"go-admin2-{self.iso3}-centroids-src-stg",
        )

    def _sql_for_tileset_source(self):
        # FIXME eventually should be name_en, name_es etc. (NOTE: fixme from existing codebase)
        return (
            pathlib.Path(f"/tmp/{self.iso3}-centroids.geojson"),
            f"""
            SELECT
                d.id as admin1_id,
                d.name as admin1_name,
                ad.name,
                ad.id,
                ad.code,
                ad.centroid
            FROM
                api_country as c,
                api_district as d,
                api_admin2 as ad
            WHERE
                c.id=d.country_id
                AND c.iso3='{self.iso3}'
                AND ad.admin1_id=d.id
        """,
        )

    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        subprocess.check_call(
            [
                "ogr2ogr",
                "-f",
                "GeoJSON",
                str(temp_source_data_file),
                self.db_helper.connection_string,
                "-sql",
                source_data_sql,
            ]
        )
