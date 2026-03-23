import abc
import dataclasses
import json
import logging
import pathlib
import subprocess
import tempfile
import time
import typing

from django.core.management.base import BaseCommand
from django.utils.functional import cached_property

from ..utils import DBHelper, validate_tilesets_id, validate_tilesets_name

logger = logging.getLogger(__name__)


class MapboxConfig(typing.NamedTuple):
    username: str
    is_prod: bool


@dataclasses.dataclass
class TilesetMetadata:
    tileset_id: str
    tileset_source_id: str

    def __post_init__(self):
        validate_tilesets_id(self.tileset_id)
        validate_tilesets_id(self.tileset_source_id)


class RecipeConfig(typing.NamedTuple):
    minzoom: int
    maxzoom: int


# TODO: Improve usages of subprocess?
class TilesetsManagerBase:
    name: str

    recipe_config: RecipeConfig

    def __init__(
        self,
        *,
        mapbox_config: MapboxConfig,
        command: BaseCommand,
    ):
        self.db_helper = DBHelper()
        self.mapbox_config = mapbox_config
        self.command = command
        # TODO: Move this to __post_init__ using dataclass?
        validate_tilesets_name(self.name)

    @cached_property
    @abc.abstractmethod
    def metadata(self) -> TilesetMetadata:
        raise NotImplementedError()

    @property
    def absolute_tileset_id(self) -> str:
        return f"{self.mapbox_config.username}.{self.metadata.tileset_id}"

    def _base_recipe(self, *, source_id: str, tileset_id: str, minzoom: int, maxzoom: int) -> dict:
        return {
            "version": 1,
            "layers": {
                tileset_id: {
                    "source": f"mapbox://tileset-source/{self.mapbox_config.username}/{source_id}",
                    "minzoom": minzoom,
                    "maxzoom": maxzoom,
                }
            },
        }

    def _get_tileset_recipe(self) -> dict:
        return self._base_recipe(
            source_id=self.metadata.tileset_source_id,
            tileset_id=self.absolute_tileset_id,
            minzoom=self.recipe_config.minzoom,
            maxzoom=self.recipe_config.maxzoom,
        )

    def log(self, message: str):
        if self.command:
            return self.command.stdout.write(message)
        return logger.info(message)

    def log_error(self, message: str):
        if self.command:
            return self.command.stderr.write(message)
        return logger.error(message)

    def log_success(self, message: str):
        if self.command:
            return self.log(self.command.style.SUCCESS(message))
        return self.log(message)

    @abc.abstractmethod
    def _sql_for_tileset_source(self) -> typing.Tuple[pathlib.Path, str]:
        raise NotImplementedError

    @abc.abstractmethod
    def _prep_source_data_ogr2ogr_run(self, *, temp_source_data_file: pathlib.Path, source_data_sql: str):
        raise NotImplementedError

    def _prep_source_data(self) -> pathlib.Path:
        self.log(f"Exporting <{self.name}>...")

        temp_source_data_file, source_data_sql = self._sql_for_tileset_source()
        if temp_source_data_file.exists():
            temp_source_data_file.unlink()

        try:
            # XXX: Without this the ogr2ogr removes csr, if it is not important we can remove this
            _source_data_sql = " ".join(source_data_sql.split())

            self._prep_source_data_ogr2ogr_run(
                temp_source_data_file=temp_source_data_file,
                source_data_sql=_source_data_sql,
            )
            self.log_success(f"<{self.name}> written to {temp_source_data_file}")
        except Exception:
            self.log_error(f"Failed to export <{self.name}>")
            raise
        return temp_source_data_file

    def _upload_source(self, source_data_file: pathlib.Path):
        try:
            tileset_source_id = self.metadata.tileset_source_id
            self.log(f"Update Mapbox tileset source for <{self.name}>: {tileset_source_id}...")
            subprocess.check_call(
                [
                    "tilesets",
                    "upload-source",
                    "--replace",
                    self.mapbox_config.username,
                    tileset_source_id,
                    str(source_data_file),
                ]
            )
        except Exception:
            self.log_error(f"Failed to update tileset source for <{self.name}>")
            raise

    def _create_tilesets(self):
        # TODO: Also handle update?
        with tempfile.NamedTemporaryFile(
            dir="/tmp",
            mode="w",
            delete=True,
            suffix=".json",
        ) as fp:
            json.dump(self._get_tileset_recipe(), fp)
            fp.flush()
            subprocess.check_call(
                [
                    "tilesets",
                    "create",
                    self.absolute_tileset_id,
                    "--recipe",
                    fp.name,
                    "--name",
                    self.name,
                ]
            )

    def _publish_tilesets(self):
        try:
            self.log(f"Publish Mapbox tilesets for <{self.name}>...")
            subprocess.check_call(["tilesets", "publish", self.absolute_tileset_id])
            self.log("Sleeping for a minute..")
            time.sleep(60)
        except Exception:
            self.log_error(f"Failed to update tilesets for <{self.name}>")
            raise

    def update(self):
        source_data_file = self._prep_source_data()
        self._upload_source(source_data_file)
        self._create_tilesets()
        self._publish_tilesets()
