from functools import cmp_to_key
from fastapi import APIRouter, Depends, Request, HTTPException
from typing import List
from ..dependencies import paging_params
from ..converters import neo_to_py
from ..pymodels import Model, Node, PropertyResponse, Term
from ..utility.version_utils import model_version_compare

router = APIRouter(
    prefix="/model",
    tags=["model"],
)

PROPERTY_NOT_EXISTS = "Property exists, but does not use an acceptable value set."
PROPERTY_ERROR_EXAMPLES = {
    "description": "Property not found or has no value set",
    "content": {
        "application/json": {
            "examples": {
                "no_value_set": {
                    "summary": "Property exists but has no value set",
                    "value": {"detail": "Property exists, but does not use an acceptable value set."}
                },
                "not_found": {
                    "summary": "Not found",
                    "value": {"detail": "Not found."}
                }
            }
        }
    }
}

@router.get(
    "/{modelHandle}/versions",
    summary="Get all versions for specified model",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or skip or limit?)"},
    },
)
def model_model_versions_get(
        request: Request, modelHandle: str) -> List[str]:
    stmt = 'MATCH (n0:model {name:$p0}) return n0 as model'
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle}
    )
    ret = []
    for row in rows:
        ret.append(neo_to_py(row['model']))

    sorted_models = sorted(ret, key=cmp_to_key(model_version_compare))

    # Apply skip and limit after sorting
    skip = request.state.skip if request.state.skip else 0
    limit = request.state.limit if request.state.limit else None

    if limit:
        sorted_models = sorted_models[skip:skip + limit]
    elif skip:
        sorted_models = sorted_models[skip:]

    result = [x.version for x in sorted_models]
    # skip and limit are handled upstream; here we return 404 when the result set is empty.
    if not result:
        raise HTTPException(status_code=404, detail="Not found.")
    
    return result


@router.get(
    "/{modelHandle}/latest-version",
    summary="Get latest version of specified model",
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or skip or limit?)"},
    },
)
def model_model_latest_version_get(
        request: Request, modelHandle: str) -> Model:
    stmt = 'MATCH (n0:model {name:$p0}) where n0.is_latest_version return n0 AS model'
    res = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle},
        raise_on_empty=False
    )
    
    if res:
        # If we found models with is_latest_version, convert and return the highest
        models = [neo_to_py(row['model']) for row in res]
        return sorted(models, key=cmp_to_key(model_version_compare))[-1]
    
    # No model with is_latest_version found, fall back to getting all versions
    stmt = 'MATCH (n0:model {name:$p0}) RETURN n0 AS model'
    res = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle}
    )
    models = [neo_to_py(row['model']) for row in res]
    return sorted(models, key=cmp_to_key(model_version_compare))[-1]


@router.get(
    "/{modelHandle}/version/{versionString}/nodes",
    summary="Get all nodes for specified model",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or versionString or skip or limit?)"},
    },
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
    summary="Get number of nodes for specified model",
    responses={
        200: {"description": "Successful Response"},
        422: {"description": "Bad parameters (modelHandle or versionString?)"},
    },
)
def model_model_handle_nodes_count_get(request: Request, modelHandle: str, versionString: str) -> int:
    stmt = 'MATCH (n0:node {model:$p0,version:$p1}) RETURN count(n0) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString}
    )
    return ret[0]['count']
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}",
    summary="Retrieve a specified node from a model",
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle?)"},
    },
)
def model_model_handle_node_node_handle_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str) -> Node:
    stmt = 'MATCH (n0:node {model:$p0,version:$p1,handle:$p2}) RETURN n0 as node'
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle}
    )
    return neo_to_py(rows[0]['node'])
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/properties",
    summary="Get all properties for specified node",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle or skip or limit?)"},
    },
)
def model_model_handle_node_node_handle_properties_get(
        request: Request,
        modelHandle: str, versionString: str,
        nodeHandle: str) -> List[PropertyResponse]:
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property) RETURN n1 as prop',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle}
    )
    for row in rows:
        prop = neo_to_py(row['prop'])
        # Convert to PropertyResponse model.
        ret.append(PropertyResponse(**prop.model_dump()))
    
    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/properties/count",
    summary="Get number of properties for specified node",
    responses={
        200: {"description": "Successful Response"},
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle?)"},
    },
)
def model_model_handle_node_node_handle_properties_count_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str) -> int:
    stmt = 'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property) RETURN count(n1) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle}
    )
    return ret[0]['count']
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}",
    summary="Retrieve a specified property from a model",
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle or propHandle?)"},
    },
)
def model_model_handle_node_node_handle_property_prop_handle_get(
        request: Request, modelHandle: str, versionString: str,
        nodeHandle: str, propHandle: str) -> PropertyResponse:
    stmt = 'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3}) RETURN n1 as prop'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle}
    )
    prop = neo_to_py(ret[0]['prop'])
    return PropertyResponse(**prop.model_dump())
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}/terms",
    summary="Get the terms (acceptable values) for specified property, if applicable to property.",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: PROPERTY_ERROR_EXAMPLES,
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle or propHandle or skip or limit?)"},
    }
)
def model_model_handle_node_node_handle_property_prop_handle_terms_get(
        request: Request,
        modelHandle: str, versionString: str,
        nodeHandle: str, propHandle: str) -> List[Term]:
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3})',
        'OPTIONAL MATCH (n1)-[r1:has_value_set]->(n3:value_set)-[r2:has_term]->(n2:term)',
        'RETURN n1 as prop, n2 as term',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle}
    )
    has_terms = False
    for row in rows:
        if row['term'] is not None:
            has_terms = True
            ret.append(neo_to_py(row['term']))

    # Property exists but has no terms
    if rows and not has_terms:
        raise HTTPException(
            status_code=404,
            detail=PROPERTY_NOT_EXISTS
        )

    return ret
    

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}/terms/count",
    summary="Get number of terms for specified property",
    responses={
        200: {"description": "Successful Response"},
        404: {"description": PROPERTY_NOT_EXISTS},
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle or propHandle?)"},
    }
)
def model_model_handle_node_node_handle_property_prop_handle_terms_count_get(request: Request, modelHandle: str, versionString: str, nodeHandle: str, propHandle: str) -> int:
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3})',
        'OPTIONAL MATCH (n1)-[r1:has_value_set]->(n3:value_set)-[r2:has_term]->(n2:term)',
        'RETURN n1 as prop, count(n2) as count'
    ])
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle}
    )

    # Property exists but has no terms
    count = rows[0]['count']
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=PROPERTY_NOT_EXISTS
        )
    return count

@router.get(
    "/{modelHandle}/version/{versionString}/node/{nodeHandle}/property/{propHandle}/term/{termValue}",
    summary="Get a specific term value for specified property",
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (modelHandle or versionString or nodeHandle or propHandle or termValue?)"},
    }
)
def model_model_handle_node_node_handle_property_prop_handle_term_term_value_get(
        request: Request,
        modelHandle: str, versionString: str,
        nodeHandle: str, propHandle: str, termValue: str) -> List[Term]:
    stmt = " ".join([
        'MATCH (n0:node {model:$p0,version:$p1,handle:$p2})-[r0:has_property]->(n1:property {handle:$p3})',
        '-[r1:has_value_set]->(n3:value_set)-[r2:has_term]->(n2:term {value:$p4})',
        'RETURN n2 as term'
    ])
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": modelHandle, "p1": versionString, "p2": nodeHandle, "p3": propHandle, "p4": termValue}
    )
    ret = []
    for row in rows:
        ret.append(neo_to_py(row['term']))
    return ret