from fastapi import APIRouter, Depends, Request
from typing import List
from ..dependencies import paging_params
from ..converters import neo_to_py
from ..pymodels import (
    Node, Property, Relationship,
    Term, Concept
)

router = APIRouter(
    prefix="/tag",
    tags=["tag"],
    )


@router.get(
    "/{key}/values",
    summary="Get list of tag values having specified tag key",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (key or skip or limit?)"},
    },
)
def tag_key_values_get(request: Request, key: str) -> List[str]:
    stmt = " ".join([
        'MATCH (n0:tag {key:$p0}) RETURN distinct n0.value as tag_value',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": key}
    )
    for row in rows:
        ret.append(row['tag_value'])
    return ret
    

@router.get(
    "/{key}/{value}/entities",
    summary="Get list of entities tagged by key:value",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (key or value or skip or limit?)"},
    },
)
def tag_key_value_entities_get(request: Request, key: str, value: str) -> List[Node | Property | Relationship | Term | Concept]:
    stmt = " ".join([
        'MATCH (n1)-[r0:has_tag]->(n0:tag {key:$p0,value:$p1}) RETURN n1 as entity',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"p0": key, "p1": value}
    )
    for row in rows:
        ret.append(neo_to_py(row['entity']))
    return ret


@router.get(
    "/{key}/{value}/entities/count",
    summary="Get number of entities tagged by key:value",
    responses={
        200: {"description": "Successful Response"},
        422: {"description": "Bad parameters (key or value?)"},
    },
)
def tag_key_value_entities_count_get(request: Request, key: str, value: str) -> int:
    stmt = 'MATCH (n1)-[r0:has_tag]->(n0:tag {key:$p0,value:$p1}) RETURN count(n1) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": key, "p1": value}
    )
    return ret[0]['count']
