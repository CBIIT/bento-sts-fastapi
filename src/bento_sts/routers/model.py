from fastapi import APIRouter, Depends, Request
from typing import List
from ..dependencies import paging_params
from ..converters import neo_to_py
from ..pymodels import Node, Property, Term

router = APIRouter(
    prefix="/model",
    tags=["model"],
    dependencies=[Depends(paging_params)],
    responses={404: {"description": "Not found."}},
    )


@router.get(
    "/{modelHandle}/version/{versionString}/nodes",
    summary="Get all nodes for specified model"
)
def model_model_handle_nodes_get(
        request: Request,
        modelHandle: str, versionString: str) -> List[Node]:
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1}) RETURN n0',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString}
    )
    ret = []
    for row in rows:
        ret.append(neo_to_py(row['n0']))
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/nodes/count",
    summary="Get number of nodes for specified model"
)
def model_model_handle_nodes_count_get(request: Request, modelHandle: str, versionString: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1}) RETURN count(n0) as count',
        f"SKIP {request.state.skip} " if request.state.skip else ""
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}",
    summary="Retrieve a specified node from a model"
)
def model_model_handle_node_node_handle_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2}) RETURN n0 as node',
        f"SKIP {request.state.skip} " if request.state.skip else ""
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/properties",
    summary="Get all properties for specified node"
)
def model_model_handle_node_node_handle_properties_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property) RETURN n1 as properties',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/properties/count",
    summary="Get number of  properties for specified node"
)
def model_model_handle_node_node_handle_properties_count_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property) RETURN count(n1) as count',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}",
    summary="Retrieve a specified property from a model"
)
def model_model_handle_node_node_handle_property_prop_handle_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str, propHandle: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3}) RETURN n1 as property',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}/terms",
    summary="Get the terms (acceptable values) for specified property, if applicable to property."
)
def model_model_handle_node_node_handle_property_prop_handle_terms_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str, propHandle: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3})-[r1:has_value_set]->(n3:value_set)-[r2:has_term]->(n2:term) RETURN n2 as terms',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}/terms/count",
    summary="Get number of  properties for specified node"
)
def model_model_handle_node_node_handle_property_prop_handle_terms_count_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str, propHandle: str):
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3})-[r1:has_value_set]->(n3:value_set)-[r2:has_term]->(n2:term) RETURN count(*) as count',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle}
    )
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}/term/{termValue}",
    summary="Retrieve a specified term from a property\'s acceptable value set"
)
def model_model_handle_node_node_handle_property_prop_handle_term_term_value_get(request: Request, termValue: str):
    stmt = " ".join([
        'MATCH (n2:term {value:$p4}) RETURN n2 as term',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p4": termValue}
    )
    return ret

