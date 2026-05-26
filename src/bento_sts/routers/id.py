from fastapi import APIRouter, Request
from ..converters import neo_to_py
from ..pymodels import MdbNanoidResponse

router = APIRouter(
    prefix="/id",
    tags=["id"],
    )


@router.get(
    "/{id}",
    summary="Get MDB entity with specified nanoid",
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (id?)"},
    },
)
def id_id_get(request: Request, id: str) -> MdbNanoidResponse:
    stmt = 'MATCH (n0 {nanoid:$p0}) RETURN n0'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": id}
    )
    return neo_to_py(ret[0]['n0'])

