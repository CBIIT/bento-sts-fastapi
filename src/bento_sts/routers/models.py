from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params

router = APIRouter(
    prefix="/models",
    tags=["models"],
    dependencies=[Depends(paging_params)],
    responses={404: {"description": "Not found."}},
    )

@router.get(
    "/",
    summary="Get info on available models"
)
def models_get(request: Request):
    stmt = " ".join(
        ['MATCH (n0:model) RETURN n0 as models ',
         f"SKIP {request.state.skip} " if request.state.skip else "",
         f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret
    

@router.get(
    "/models/count",
    summary="Get number of available models"
)
def models_count_get(request: Request):
    stmt = 'MATCH (n0:model) RETURN count(*) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret
