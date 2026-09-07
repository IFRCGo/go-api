import json
import os
import tempfile
import weakref

import requests

from api.logger import logger


def _safe_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


class _CachedPaginated:
    """Iterable wrapper around a streaming generator factory.

    The first iteration drains the source generator and tees each record into a
    JSONL cache file under /tmp/. Subsequent iterations replay from that cache.
    Memory stays bounded to one record at a time, even when the caller iterates
    the same result more than once (as sync_molnix does for tags + main loop).
    """

    def __init__(self, source_factory, label=""):
        self._source_factory = source_factory
        self._label = label
        fd, self._cache_path = tempfile.mkstemp(suffix=".jsonl", prefix="molnix_paginated_")
        os.close(fd)
        self._cached = False
        self._iter_count = 0
        weakref.finalize(self, _safe_unlink, self._cache_path)

    def __iter__(self):
        self._iter_count += 1
        if self._cached:
            logger.warning(
                "_CachedPaginated[%s] re-iteration #%d from cache %s",
                self._label,
                self._iter_count,
                self._cache_path,
            )
            with open(self._cache_path) as f:
                for line in f:
                    yield json.loads(line)
            return
        logger.warning(
            "_CachedPaginated[%s] first iteration #%d streaming from source -> %s",
            self._label,
            self._iter_count,
            self._cache_path,
        )
        with open(self._cache_path, "w") as f:
            for item in self._source_factory():
                f.write(json.dumps(item))
                f.write("\n")
                yield item
        self._cached = True


class MolnixApi:

    access_token = None

    def __init__(self, url="https://api.ifrc-staging.rpm.molnix.com/api/", username=None, password=None):
        if username is None or password is None:
            raise Exception("username or password not supplied")
        self.url = url
        self.username = username
        self.password = password

    def call_api(self, path, method="GET", params={}):
        url = self.url + path
        headers = {}
        if self.access_token:
            headers["Authorization"] = "Bearer %s" % self.access_token
        if method == "GET":
            res = requests.get(url, params=params, headers=headers)
        if method == "POST":
            res = requests.post(url, json=params, headers=headers)
        if res.status_code > 300:
            raise Exception("call to %s failed" % url)  # FIXME: print msg from API
        return res.json()

    def call_api_paginated(self, path, response_key=None, params={}):
        page = 1
        while True:
            params["page"] = page
            data = self.call_api(path=path, params=params)
            if response_key:
                data = data[response_key]["data"]
            if len(data) == 0:
                return
            yield from data
            page += 1

    def login(self):
        params = {"username": self.username, "password": self.password}
        response = self.call_api("login", "POST", params)
        if "access_token" not in response.keys():
            raise Exception("unexpected response to login")
        self.access_token = response["access_token"]
        return True

    def get_tags(self):
        return self.call_api_paginated(path="tags")["tags"]

    def get_tag_groups(self, id):
        return self.call_api(path="tags/edit/%d" % id)["tag"]["groups"]

    def get_open_positions(self):
        # return self.call_api_paginated(path="positions", response_key="positions")
        return self.call_api(path="positions/open")

    def get_not_only_open_positions(self):
        # return self.call_api_paginated(path="positions", response_key="positions")
        return _CachedPaginated(
            lambda: self.call_api_paginated(path="positions", response_key="positions", params={"limit": 999999}),
            label="positions",
        )

    def get_deployments(self):
        deployments_filter = {
            "persontags": [],
            "personoperator": "",
            "deploymenttags": [],
            "deploymentoperator": "",
            "orderBy": "ID",
            "orderType": "DESC",
            "userroles": [],
            "criterias": "[]",
        }
        params = {"filter": json.dumps(deployments_filter)}
        return _CachedPaginated(
            lambda: self.call_api_paginated(path="deployments", response_key="deployments", params=params),
            label="deployments",
        )

    """
        WARNING: If position is not found or generates an error, we return None
    """

    def get_position(self, id):
        try:
            return self.call_api(path="positions/%d" % id)
        except Exception:
            return None

    def get_deployment(self, id):
        try:
            return self.call_api(path="deployments/%d" % id)
        except Exception:
            return None

    def get_countries(self):
        countries = self.call_api(path="countries")
        countries_list = countries["countries"]
        countries_dict = {}
        for country in countries_list:
            countries_dict[country["id"]] = country["code"]
        return countries_dict

    def logout(self):
        self.call_api("logout")
        return True
