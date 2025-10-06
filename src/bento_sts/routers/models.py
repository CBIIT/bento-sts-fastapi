from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params
from typing import List
from ..pymodels import Model
from ..converters import toModel

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
def models_get(request: Request) -> List[Model]:
    stmt = " ".join(
        ['MATCH (n0:model) RETURN n0 as model',
         f"SKIP {request.state.skip} " if request.state.skip else "",
         f"LIMIT {request.state.limit}" if request.state.limit else ""])
    rows = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    # ret = []
    # for row in rows:
    #     ret.append(toModel(row['model']))
    return rows
    

@router.get(
    "/models/count",
    summary="Get number of available models"
)
def models_count_get(request: Request) -> int:
    stmt = 'MATCH (n0:model) RETURN count(*) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret[0]['count']
