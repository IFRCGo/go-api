"""
Elasticsearch alias-swap utilities shared by bulk-indexing management commands.

Usage pattern
-------------
1. Call ``create_versioned_index`` to create an empty index with the correct
   settings and mapping, ready to receive bulk writes.
2. Write all documents into the returned versioned index name.
3. Call ``swap_alias`` to atomically move the alias from the old index(es) to
   the new one.  The application keeps reading from the alias without interruption.
4. Optionally delete the previous index(es) returned by ``get_alias_targets``.
"""

from datetime import datetime, timezone
from typing import List, Optional

from elasticsearch.client import IndicesClient


def make_versioned_index_name(alias_name: str) -> str:
    """Return ``<alias_name>_YYYYMMDDHHMMSS`` using the current UTC timestamp."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{alias_name}_{ts}"


def get_alias_targets(indices_client: IndicesClient, alias_name: str) -> List[str]:
    """
    Return the concrete index names currently pointed to by *alias_name*.

    Returns an empty list when the alias does not exist yet (first run).
    """
    try:
        if not indices_client.exists_alias(name=alias_name):
            return []
        result = indices_client.get_alias(name=alias_name)
        return list(result.keys())
    except Exception:
        return []


def swap_alias(
    indices_client: IndicesClient,
    alias_name: str,
    new_index: str,
    old_indexes: Optional[List[str]] = None,
) -> None:
    """
    Atomically point *alias_name* to *new_index* via the ES ``_aliases`` API.

    All remove + add actions are sent in a single request, ensuring the alias
    always points to at least one index.  If *old_indexes* is ``None`` it is
    resolved via :func:`get_alias_targets` before building the action list.
    """
    if old_indexes is None:
        old_indexes = get_alias_targets(indices_client, alias_name)

    actions: List[dict] = []
    for idx in old_indexes:
        if idx != new_index:
            actions.append({"remove": {"index": idx, "alias": alias_name}})
    actions.append({"add": {"index": new_index, "alias": alias_name}})

    indices_client.update_aliases(body={"actions": actions})


def create_versioned_index(
    es_client,
    alias_name: str,
    settings: dict,
    mapping: dict,
) -> str:
    """
    Create a fresh versioned index ready for bulk writes.

    * Generates a name like ``<alias_name>_YYYYMMDDHHMMSS``.
    * Deletes any same-minute duplicate that already exists (safe re-run).
    * Applies *settings* then *mapping*.
    * Does **not** swap the alias – call :func:`swap_alias` after a successful
      ingestion run.

    Returns the versioned index name.
    """
    indices_client = IndicesClient(client=es_client)
    versioned_name = make_versioned_index_name(alias_name)

    if indices_client.exists(versioned_name):
        indices_client.delete(index=versioned_name)

    indices_client.create(index=versioned_name, body=settings)
    indices_client.put_mapping(index=versioned_name, body=mapping)

    return versioned_name
