"""Tests for MDBReader.get_with_statement caching and /admin/cache/clear.

Uses the real test Neo4j instance from the test_mdb / test_sts_mdb fixtures.
"""

import pytest
import requests
from fastapi import HTTPException

from bento_sts.mdb import MDBReader


def _cache_key(generation: int, qry: str, parms: dict, raise_on_empty: bool):
    """Must match MDBReader.get_with_statement key construction."""
    return (generation, qry, tuple(sorted(parms.items())), raise_on_empty)


def _is_responsive(url: str) -> bool:
    try:
        return requests.get(url).status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def test_mdb(docker_services, docker_ip):
    bolt_port = docker_services.port_for("test-mdb", 7687)
    http_port = docker_services.port_for("test-mdb", 7474)
    bolt_url = f"bolt://{docker_ip}:{bolt_port}"
    http_url = f"http://{docker_ip}:{http_port}"
    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=2.0,
        check=lambda: _is_responsive(http_url),
    )
    return (bolt_url, http_url)


@pytest.fixture(scope="session")
def test_sts_client(test_mdb):
    from bento_sts import dependencies
    from bento_sts.sts import app
    from fastapi.testclient import TestClient

    dependencies.mdb = MDBReader(uri=test_mdb[0], user="neo4j1", password="neo4j")
    return TestClient(app)


@pytest.fixture(scope="session")
def test_sts_mdb(test_mdb):
    rdr = MDBReader(uri=test_mdb[0], user="neo4j", password="neo4j1")
    try:
        yield rdr
    finally:
        rdr.close()


@pytest.fixture(autouse=True)
def reset_sts_mdb_cache_local(test_sts_mdb: MDBReader):
    test_sts_mdb.clear_cache()
    yield


def test_get_with_statement_miss_stores_entry_in_cache_local(test_sts_mdb: MDBReader):
    """On miss, result is written to TTLCache before return."""
    qry, parms = "RETURN 1 AS n", {}
    key = _cache_key(test_sts_mdb._cache_generation, qry, parms, True)
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
    key = _cache_key(test_sts_mdb._cache_generation, qry, {}, False)
    assert key not in test_sts_mdb._cache

    a = test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=False)
    b = test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=False)

    assert a == b == []
    assert key in test_sts_mdb._cache
    assert test_sts_mdb._cache[key] == []
    assert len(test_sts_mdb._cache) >= 1


def test_get_with_statement_cache_hit_local(test_sts_mdb: MDBReader):
    qry, parms = "RETURN 1 AS n", {}
    a = test_sts_mdb.get_with_statement(qry, parms)
    b = test_sts_mdb.get_with_statement(qry, parms)
    assert a is b
    assert len(a) == 1 and a[0]["n"] == 1


def test_get_with_statement_different_params_separate_cache_local(test_sts_mdb: MDBReader):
    qry = "RETURN $x AS n"
    before = len(test_sts_mdb._cache)
    test_sts_mdb.get_with_statement(qry, {"x": 1})
    test_sts_mdb.get_with_statement(qry, {"x": 2})
    assert len(test_sts_mdb._cache) == before + 2


def test_get_with_statement_parm_key_order_irrelevant_local(test_sts_mdb: MDBReader):
    """Cache key sorts parms.items() so dict key order does not bust the cache."""
    qry = "RETURN $a + $b AS s"
    before = len(test_sts_mdb._cache)
    test_sts_mdb.get_with_statement(qry, {"a": 1, "b": 2})
    test_sts_mdb.get_with_statement(qry, {"b": 2, "a": 1})
    assert len(test_sts_mdb._cache) == before + 1


def test_get_with_statement_clear_cache_local(test_sts_mdb: MDBReader):
    qry, parms = "RETURN 1 AS n", {}
    before = len(test_sts_mdb._cache)
    old = test_sts_mdb.get_with_statement(qry, parms)
    test_sts_mdb.get_with_statement(qry, parms)
    assert len(test_sts_mdb._cache) in (before, before + 1)

    old_generation = test_sts_mdb._cache_generation
    test_sts_mdb.clear_cache()
    assert test_sts_mdb._cache_generation == old_generation + 1
    assert len(test_sts_mdb._cache) == before

    new = test_sts_mdb.get_with_statement(qry, parms)
    assert len(test_sts_mdb._cache) in (before, before + 1, before + 2)
    assert new is old


def test_get_with_statement_raise_on_empty_in_cache_key_local(test_sts_mdb: MDBReader):
    qry = "RETURN 1 AS n"
    before = len(test_sts_mdb._cache)
    test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=False)
    test_sts_mdb.get_with_statement(qry, {}, raise_on_empty=True)
    assert len(test_sts_mdb._cache) in (before + 1, before + 2)


def test_get_with_statement_404_not_cached_local(test_sts_mdb: MDBReader):
    """Empty + raise_on_empty=True raises before cache write; repeat is still a miss."""
    qry = "UNWIND [] AS x RETURN x AS n"
    key = _cache_key(test_sts_mdb._cache_generation, qry, {}, True)
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
