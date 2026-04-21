from fastapi import APIRouter, Depends, Request
from typing import List
from ..dependencies import paging_params_tags
from ..converters import neo_to_py
from ..pymodels import Tag

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    )


@router.get(
    "/",
    summary="Get all tag nodes in MDB",
    dependencies=[Depends(paging_params_tags)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (skip or limit?)"},
    },
)
def tags_get(request: Request) -> List[Tag]:
    stmt = " ".join([
        'MATCH (n0:tag) RETURN n0 as tag',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    for row in rows:
        ret.append(neo_to_py(row['tag']))
    return ret


@router.get(
    "/count",
    summary="Get number of tags present in MDB",
    responses={
        200: {"description": "Successful Response"},
    },
)
def tags_count_get(request: Request) -> int:
    stmt = 'MATCH (n0:tag) RETURN count(n0) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret[0]['count']
