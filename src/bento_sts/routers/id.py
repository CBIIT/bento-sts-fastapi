from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params

router = APIRouter(
    prefix="/id",
    tags=["id"],
    responses={404: {"description": "Not found."}},
    )


@router.get(
    "/{id}",
    summary="Get MDB entity with specified nanoid"
)
def id_id_get(request: Request, id: str):
    stmt = 'MATCH (n0 {nanoid:$p0}) RETURN n0'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": id}
    )
    return ret
