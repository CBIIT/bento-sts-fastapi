"""Tests for MDBReader.get_with_statement caching and /admin/cache/clear.

Uses the real test Neo4j instance from the test_mdb / test_sts_mdb fixtures.
"""

import pytest
from fastapi import HTTPException

from bento_sts.mdb import MDBReader


def _cache_key(qry: str, parms: dict, raise_on_empty: bool):
    """Must match MDBReader.get_with_statement key construction."""
    return (qry, tuple(sorted(parms.items())), raise_on_empty)


@pytest.fixture(autouse=True)
def reset_sts_mdb_cache_local(test_sts_mdb: MDBReader):
    test_sts_mdb.clear_cache()
    yield


def test_get_with_statement_miss_stores_entry_in_cache_local(test_sts_mdb: MDBReader):
    """On miss, result is written to TTLCache before return."""
    qry, parms = "RETURN 1 AS n", {}
    key = _cache_key(qry, parms, True)
    assert key not in test_sts_mdb._cache
    assert len(test_sts_mdb._cache) == 0

    out = test_sts_mdb.get_with_statement(qry, parms)

    assert key in test_sts_mdb._cache
    assert len(test_sts_mdb._cache) == 1
    assert test_sts_mdb._cache[key] is out
    assert len(out) == 1 and out[0]["n"] == 1


def test_get_with_statement_returns_stored_object_identity_local(test_sts_mdb: MDBReader):
    """Second call returns the same list object from _cache."""
    qry = "RETURN $k AS n"
    parms = {"k": 42}
    first = test_sts_mdb.get_with_statement(qry, parms)
    second = test_sts_mdb.get_with_statement(qry, parms)
    assert first is second
    assert len(first) == 1 and first[0]["n"] == 42


def test_get_with_statement_empty_list_stored_on_miss_local(test_sts_mdb: MDBReader):
    """raise_on_empty=False: zero-row result is still stored in _cache."""
    qry = "UNWIND [] AS x RETURN x AS n"
    key = _cache_key(qry, {}, False)
    assert key not in test_sts_mdb._cache

    a = test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=False)
    b = test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=False)

    assert a == b == []
    assert key in test_sts_mdb._cache
    assert test_sts_mdb._cache[key] == []
    assert len(test_sts_mdb._cache) == 1


def test_get_with_statement_cache_hit_local(test_sts_mdb: MDBReader):
    qry, parms = "RETURN 1 AS n", {}
    a = test_sts_mdb.get_with_statement(qry, parms)
    b = test_sts_mdb.get_with_statement(qry, parms)
    assert a is b
    assert len(a) == 1 and a[0]["n"] == 1


def test_get_with_statement_different_params_separate_cache_local(test_sts_mdb: MDBReader):
    qry = "RETURN $x AS n"
    test_sts_mdb.get_with_statement(qry, {"x": 1})
    test_sts_mdb.get_with_statement(qry, {"x": 2})
    assert len(test_sts_mdb._cache) == 2


def test_get_with_statement_parm_key_order_irrelevant_local(test_sts_mdb: MDBReader):
    """Cache key sorts parms.items() so dict key order does not bust the cache."""
    qry = "RETURN $a + $b AS s"
    test_sts_mdb.get_with_statement(qry, {"a": 1, "b": 2})
    test_sts_mdb.get_with_statement(qry, {"b": 2, "a": 1})
    assert len(test_sts_mdb._cache) == 1


def test_get_with_statement_clear_cache_local(test_sts_mdb: MDBReader):
    qry, parms = "RETURN 1 AS n", {}
    test_sts_mdb.get_with_statement(qry, parms)
    test_sts_mdb.get_with_statement(qry, parms)
    assert len(test_sts_mdb._cache) == 1

    test_sts_mdb.clear_cache()
    assert len(test_sts_mdb._cache) == 0

    test_sts_mdb.get_with_statement(qry, parms)
    assert len(test_sts_mdb._cache) == 1


def test_get_with_statement_raise_on_empty_in_cache_key_local(test_sts_mdb: MDBReader):
    qry = "RETURN 1 AS n"
    test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=False)
    test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=True)
    assert len(test_sts_mdb._cache) == 2


def test_get_with_statement_404_not_cached_local(test_sts_mdb: MDBReader):
    """Empty + raise_on_empty=True raises before cache write; repeat is still a miss."""
    qry = "UNWIND [] AS x RETURN x AS n"
    key = _cache_key(qry, {}, True)
    with pytest.raises(HTTPException) as exc:
        test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=True)
    assert exc.value.status_code == 404

    assert key not in test_sts_mdb._cache

    with pytest.raises(HTTPException):
        test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=True)


def test_admin_cache_clear_route_local(test_sts_client):
    resp = test_sts_client.get("/v2/admin/cache/clear")
    assert resp.status_code == 200
    assert resp.json() == {"status": "cache cleared"}
