import pytest
import requests
import os
from fastapi.testclient import TestClient
from bento_sts.sts import app
from bento_sts.mdb import MDBReader
from requests.exceptions import ConnectionError


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session", params=["local", "cicd"],
                ids=["local", "cicd"])
def test_mdb(request):
    if request.param == "local":
        docker_services = request.getfixturevalue("docker_services")
        docker_ip = request.getfixturevalue("docker_ip")
        bolt_port = docker_services.port_for("test-mdb", 7687)
        http_port = docker_services.port_for("test-mdb", 7474)
        bolt_url = f"bolt://{docker_ip}:{bolt_port}"
        http_url = f"http://{docker_ip}:{http_port}"
        docker_services.wait_until_responsive(
            timeout=30.0, pause=2.0,
            check=lambda: is_responsive(http_url)
        )
    elif request.param == "cicd":
        bolt_url = "bolt://localhost:7687"
        http_url = "http://localhost:7474"
        pass
    else:
        RuntimeError("test_mdb fixture: param must be either 'local' or 'cicd'")
    return (bolt_url, http_url)


@pytest.fixture(scope="session")
def test_sts_client(test_mdb):
    os.environ['NEO4J_MDB_URI'] = test_mdb[0]
    os.environ['NEO4J_MDB_USER'] = 'neo4j1'
    os.environ['NEO4J_MDB_PASS'] = 'neo4j'
    return TestClient(app)


@pytest.fixture(scope="session")
def test_sts_mdb(test_mdb):
    rdr = MDBReader(uri=test_mdb[0],
                    user='neo4j',
                    password='neo4j1')
    try:
        yield rdr
    finally:
        rdr.close()

# @pytest.fixture(scope="session")
# def docker_setup():
#     return ["up -d --wait"]


@pytest.fixture(scope="session")
def docker_compose_project_name():
    return "bento-sts-test"

