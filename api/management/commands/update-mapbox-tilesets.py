import dataclasses
import os
import typing

from django.conf import settings
from django.core.management.base import BaseCommand

from mapbox.tilesets.base import MapboxConfig, TilesetsManagerBase
from mapbox.tilesets.managers import (
    Admin2CentroidsTilesetsManager,
    Admin2TilesetsManager,
    CountryCentroidsTilesetsManager,
    CountryTilesetsManager,
    DistrictCentroidsTilesetsManager,
    DistrictTilesetsManager,
)


class Command(BaseCommand):
    help = "This command produces a countries.geojson and districts.geojson, and uploads them to Mapbox. It is the source for all GO Maps."  # noqa: E501

    missing_args_message = "Argument missing. Specify --update-countries, --update-districts or --update-all."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-countries",
            action="store_true",
            help="Update tileset for countries",
        )
        parser.add_argument(
            "--update-districts",
            action="store_true",
            help="Update tileset for districts",
        )
        parser.add_argument("--update-admin2", help="Update admin2 tileset for this country ISO")
        parser.add_argument(
            "--update-all",
            action="store_true",
            help="Update tileset for countries and districts",
        )

    def confirmation_prompt(
        self,
        mapbox_config: MapboxConfig,
        managers: typing.Sequence[TilesetsManagerBase],
    ) -> bool:
        self.stdout.write(f"Mapbox Configuration used: {mapbox_config._asdict()}")
        self.stdout.write("Tileset Configuration to be updated:")
        for manager in managers:
            self.stdout.write(self.style.WARNING(f"## {manager.name}"))
            for key, value in dataclasses.asdict(manager.metadata).items():
                self.stdout.write(f"{key:30}: {self.style.WARNING(value)}")

        confirm = "n"
        try:
            confirm = input("Are you sure you want to continue? [y/N]: ")
        except KeyboardInterrupt:
            ...

        if confirm.lower() != "y":
            self.stdout.write(self.style.WARNING("Operation cancelled."))
            return False

        self.stdout.write(self.style.SUCCESS("Confirmed. Running command..."))
        return True

    def handle(self, *args, **options):
        if os.getenv("MAPBOX_ACCESS_TOKEN") is None:
            raise Exception("MAPBOX_ACCESS_TOKEN must be set")

        staging: bool = settings.GO_ENVIRONMENT != "production"
        mapbox_config = MapboxConfig(
            username="go-ifrc",
            is_prod=not staging,
        )

        to_update_managers: typing.Sequence[TilesetsManagerBase] = []

        if options["update_countries"] or options["update_all"]:
            country_manager = CountryTilesetsManager(command=self, mapbox_config=mapbox_config)
            country_centroid_manager = CountryCentroidsTilesetsManager(
                command=self,
                mapbox_config=mapbox_config,
            )
            to_update_managers.extend(
                [
                    country_manager,
                    country_centroid_manager,
                ]
            )

        if options["update_districts"] or options["update_all"]:
            district_manager = DistrictTilesetsManager(command=self, mapbox_config=mapbox_config)
            district_centroid_manager = DistrictCentroidsTilesetsManager(
                command=self,
                mapbox_config=mapbox_config,
            )
            to_update_managers.extend(
                [
                    district_manager,
                    district_centroid_manager,
                ]
            )

        if options["update_admin2"]:
            iso3 = options["update_admin2"]
            admin2_manager = Admin2TilesetsManager(
                command=self,
                mapbox_config=mapbox_config,
                iso3=iso3,
            )
            admin2_centroid_manager = Admin2CentroidsTilesetsManager(
                command=self,
                mapbox_config=mapbox_config,
                iso3=iso3,
            )
            to_update_managers.extend(
                [
                    admin2_manager,
                    admin2_centroid_manager,
                ]
            )

        if not self.confirmation_prompt(mapbox_config, to_update_managers):
            return

        for to_update_manager in to_update_managers:
            to_update_manager.update()
