import os
import struct
import time

import pyodbc
from azure.identity import AzureCliCredential

SQL_COPT_SS_ACCESS_TOKEN = 1256
SQL_ATTR_LOGIN_TIMEOUT = 103
SQL_ATTR_CONNECTION_TIMEOUT = 113
SCOPE = "https://database.windows.net/.default"

_cred = AzureCliCredential()
_token_cache = {"token_struct": None, "exp": 0}


def _get_access_token_struct() -> bytes:
    import time as _t

    now = _t.time()
    if _token_cache["token_struct"] and now < (_token_cache["exp"] - 120):
        return _token_cache["token_struct"]

    tok = _cred.get_token(SCOPE)
    tb = tok.token.encode("utf-16-le")
    ts = struct.pack("<I", len(tb)) + tb
    _token_cache["token_struct"] = ts
    _token_cache["exp"] = tok.expires_on
    return ts


def get_fabric_connection() -> pyodbc.Connection:
    server = os.getenv("FABRIC_SQL_SERVER")
    database = os.getenv("FABRIC_SQL_DATABASE")
    if not server or not database:
        raise RuntimeError("Missing FABRIC_SQL_SERVER or FABRIC_SQL_DATABASE")

    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={server};"
        f"Database={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "MARS_Connection=no;"
        "Application Name=go-api-fabric;"
        "Connection Timeout=120;"
        "LoginTimeout=120;"
    )

    token_struct = _get_access_token_struct()
    attrs = {
        SQL_COPT_SS_ACCESS_TOKEN: token_struct,
        SQL_ATTR_LOGIN_TIMEOUT: 120,
        SQL_ATTR_CONNECTION_TIMEOUT: 120,
    }

    last = None
    for i in range(4):
        try:
            return pyodbc.connect(conn_str, attrs_before=attrs, timeout=30)
        except pyodbc.Error as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def fetch_all(cursor, sql: str, params: tuple | None = None, limit: int = 50) -> list[dict]:
    params = params or ()
    cursor.execute(sql, params)
    cols = [c[0] for c in cursor.description]
    rows = cursor.fetchmany(limit)  # cur.fetchall() for everything, i used limit for testing purposes
    return [dict(zip(cols, row)) for row in rows]
