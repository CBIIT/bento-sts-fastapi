from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    dependencies=[Depends(paging_params)],
    responses={404: {"description": "Not found."}},
    )


@router.get(
    "/",
    summary="Get all tag nodes in MDB"
)
def tags_get(request: Request):
    stmt = " ".join([
        'MATCH (n0:tag) RETURN n0 as tags',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret


@router.get(
    "/count",
    summary="Get number of tags present in MDB"
)
def tags_count_get(request: Request):
    stmt = 'MATCH (n0:tag) RETURN count(*) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret
