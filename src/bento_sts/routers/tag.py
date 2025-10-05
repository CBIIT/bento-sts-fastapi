from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params

router = APIRouter(
    prefix="/tag",
    tags=["tag"],
    dependencies=[Depends(paging_params)],
    responses={404: {"description": "Not found."}},
    )


@router.get(
    "/{key}/values",
    summary="Get list of tags having specified tag key"
)
def tag_key_values_get(request: Request, key: str):
    stmt = " ".join([
        'MATCH (n0:tag {key:$p0}) RETURN n0 as tags',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": key}
    )
    return ret
    

@router.get(
    "/{key}/{value}/entities",
    summary="Get list of entities tagged by key:value"
)
def tag_key_value_entities_get(request: Request, key: str, value: str):
    stmt = " ".join([
        'MATCH (n1)-[r0:has_tag]->(n0:tag {key:$p0,value:$p1}) RETURN n1 as entities',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": key, "p1": value}
    )
    return ret


@router.get(
    "/{key}/{value}/entities/count",
    summary="Get number of entities tagged by key:value"
)
def tag_key_value_entities_count_get(request: Request, key: str, value: str):
    stmt = " ".join([
        'MATCH (n1)-[r0:has_tag]->(n0:tag {key:$p0,value:$p1}) RETURN count(*) as count',
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": key, "p1": value}
    )
    return ret
