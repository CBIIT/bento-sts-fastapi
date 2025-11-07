import pytest
import requests
import os
from fastapi.testclient import TestClient
from bento_sts.sts import app
from bento_sts.mdb import MDBReader
from requests.exceptions import ConnectionError
# from time import sleep

# wait=10


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session")
def test_mdb(docker_services, docker_ip):
    bolt_port = docker_services.port_for("test-mdb", 7687)
    http_port = docker_services.port_for("test-mdb", 7474)
    bolt_url = f"bolt://{docker_ip}:{bolt_port}"
    http_url = f"http://{docker_ip}:{http_port}"
    docker_services.wait_until_responsive(
        timeout=20.0, pause=1.0,
        check=lambda: is_responsive(http_url)
    )
    return (bolt_url, http_url)

@pytest.fixture(scope="session")
def test_mdb_7687():
    return ("bolt://localhost:7687", "http://localhost:7474")

@pytest.fixture(scope="session")
def test_sts_client(test_mdb):
    os.putenv('NEO4J_MDB_URI',test_mdb[0])
    os.putenv('NEO4J_MDB_USER','neo4j1')
    os.putenv('NEO4J_MDB_PASS','neo4j')
    return TestClient(app)

@pytest.fixture(scope="session")
def test_sts_mdb(test_mdb):
    os.putenv('NEO4J_MDB_URI',test_mdb[0])
    os.putenv('NEO4J_MDB_USER','neo4j1')
    os.putenv('NEO4J_MDB_PASS','neo4j')
    rdr = MDBReader()
    try:
        yield rdr
    finally:
        rdr.close()

    
    
@pytest.fixture(scope="session")
def docker_compose_project_name():
    return "bento-sts-test"

