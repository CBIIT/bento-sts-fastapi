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


def _execute_write_query(test_sts_mdb, query: str, params: dict = {}):
    """Helper function to execute Neo4j write queries"""
    def txn_write(tx):
        result = tx.run(query, parameters=params)
        return [rec for rec in result]
    
    with test_sts_mdb.driver.session() as session:
        result = session.execute_write(txn_write)
        return result


@pytest.fixture(scope="function")
def test_data_setup(test_sts_mdb):
    """
    Create test data for should_use_null_cde flag tests.
    Test data is created and cleaned up for each test function (function scope).
    """
    
    # Clean up existing test data - split into multiple steps for reliability
    cleanup_stmts = [
        # 1. Remove tags
        "MATCH (t:tag {key: 'useNullCDE'}) DETACH DELETE t",
        # 2. Remove concept relationships from properties
        "MATCH (p:property)-[r:has_concept]->() DELETE r",
        # 3. Remove properties
        "MATCH (n:node {model: 'TestModel', version: '1.0'})-[r:has_property]->(p:property) DELETE r, p",
        # 4. Remove nodes
        "MATCH (n:node {model: 'TestModel', version: '1.0'}) DELETE n",
        # 5. Remove concepts
        "MATCH (c:concept {handle: 'age_concept'}) DETACH DELETE c",
        # 6. Remove CDE/terms
        "MATCH (cde:term {origin_id: '2184592'}) DETACH DELETE cde",
        # 7. Remove value sets
        "MATCH (vs:value_set {handle: '2184592|1.0'}) DETACH DELETE vs",
        # 8. Remove value set terms
        "MATCH (t:term {value: '18-25', origin_name: 'caDSR'}) DETACH DELETE t",
        "MATCH (t:term {value: '26-35', origin_name: 'caDSR'}) DETACH DELETE t",
    ]
    
    for cleanup_stmt in cleanup_stmts:
        try:
            _execute_write_query(test_sts_mdb, cleanup_stmt, {})
        except:
            pass  # Data may not exist
    
    # 1. Create test node
    create_node_stmt = """
    CREATE (n:node {model: "TestModel", version: "1.0", handle: "TestModel:1.0"})
    RETURN n
    """
    _execute_write_query(test_sts_mdb, create_node_stmt, {})
    
    # 2. Create entity
    create_entity_stmt = """
    CREATE (e:node {model: "TestModel", version: "1.0", handle: "TestModel:1.0.Demographic"})
    RETURN e
    """
    _execute_write_query(test_sts_mdb, create_entity_stmt, {})
    
    # 3. Create property with multiple useNullCDE tags (value can be True or "Yes")
    create_prop_multiple_tags_stmt = """
    MATCH (e:node {handle: "TestModel:1.0.Demographic"})
    CREATE (p:property {
        handle: "age",
        model: "TestModel",
        version: "1.0"
    })
    CREATE (e)-[:has_property]->(p)
    CREATE (t1:tag {key: "useNullCDE", value: true})
    CREATE (t2:tag {key: "useNullCDE", value: "Yes"})
    CREATE (p)-[:has_tag]->(t1)
    CREATE (p)-[:has_tag]->(t2)
    RETURN p, t1, t2
    """
    _execute_write_query(test_sts_mdb, create_prop_multiple_tags_stmt, {})
    
    # 4. Create property with single useNullCDE tag with string "Yes"
    create_prop_yes_stmt = """
    MATCH (e:node {handle: "TestModel:1.0.Demographic"})
    CREATE (p:property {
        handle: "gender",
        model: "TestModel",
        version: "1.0"
    })
    CREATE (e)-[:has_property]->(p)
    CREATE (t:tag {key: "useNullCDE", value: "Yes"})
    CREATE (p)-[:has_tag]->(t)
    RETURN p, t
    """
    _execute_write_query(test_sts_mdb, create_prop_yes_stmt, {})
    
    # 5. Create property with single useNullCDE tag with string "No"
    create_prop_no_stmt = """
    MATCH (e:node {handle: "TestModel:1.0.Demographic"})
    CREATE (p:property {
        handle: "race",
        model: "TestModel",
        version: "1.0"
    })
    CREATE (e)-[:has_property]->(p)
    CREATE (t:tag {key: "useNullCDE", value: "No"})
    CREATE (p)-[:has_tag]->(t)
    RETURN p, t
    """
    _execute_write_query(test_sts_mdb, create_prop_no_stmt, {})
    
    print("✅ Test data setup complete")
    yield test_sts_mdb  # Return test_sts_mdb for test execution
    
    # Cleanup (teardown) - clean up after each test (split into multiple steps)
    cleanup_final_stmts = [
        # 1. Remove tags
        "MATCH (t:tag {key: 'useNullCDE'}) DETACH DELETE t",
        # 2. Remove concept relationships from properties
        "MATCH (p:property)-[r:has_concept]->() DELETE r",
        # 3. Remove properties
        "MATCH (n:node {model: 'TestModel', version: '1.0'})-[r:has_property]->(p:property) DELETE r, p",
        # 4. Remove nodes
        "MATCH (n:node {model: 'TestModel', version: '1.0'}) DELETE n",
        # 5. Remove concepts
        "MATCH (c:concept {handle: 'age_concept'}) DETACH DELETE c",
        # 6. Remove CDE/terms
        "MATCH (cde:term {origin_id: '2184592'}) DETACH DELETE cde",
        # 7. Remove value sets
        "MATCH (vs:value_set {handle: '2184592|1.0'}) DETACH DELETE vs",
        # 8. Remove value set terms
        "MATCH (t:term {value: '18-25', origin_name: 'caDSR'}) DETACH DELETE t",
        "MATCH (t:term {value: '26-35', origin_name: 'caDSR'}) DETACH DELETE t",
    ]
    
    for cleanup_stmt in cleanup_final_stmts:
        try:
            _execute_write_query(test_sts_mdb, cleanup_stmt, {})
        except:
            pass
    print("✅ Test data cleanup complete")