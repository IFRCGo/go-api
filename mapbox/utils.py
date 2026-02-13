import re

from django.conf import settings


class DBHelper:
    def __init__(self):
        db = settings.DATABASES["default"]
        DB_HOST = db["HOST"]
        DB_NAME = db["NAME"]
        DB_USER = db["USER"]
        DB_PASSWORD = db["PASSWORD"]
        DB_PORT = db["PORT"]

        self.connection_string = "PG:host={} dbname={} user={} password={} port={}".format(
            DB_HOST,
            DB_NAME,
            DB_USER,
            DB_PASSWORD,
            DB_PORT,
        )


def validate_tilesets_name(value: str) -> None:
    error_message = f'<{value}>, Only alphanumeric characters, spaces, "-", "_", and "." allowed. 64 characters max'

    if len(value) == 0 or len(value) > 64:
        raise ValueError(error_message)

    pattern = r"^[A-Za-z0-9 _\-.]{1,64}$"
    if not re.fullmatch(pattern, value):
        raise ValueError(error_message)


def validate_tilesets_id(value: str) -> None:
    error_message = f'<{value}>, Must be no more than 32 characters and only include "-", "_", and alphanumeric characters.'
    if len(value) == 0 or len(value) > 64:
        raise ValueError(error_message)

    pattern = r"^[A-Za-z0-9_-]{1,32}$"
    if not bool(re.fullmatch(pattern, value)):
        raise ValueError(error_message)
