from fastapi import APIRouter, Depends, Request
from typing import List

from pydantic import BaseModel

from ..dependencies import paging_params
from ..converters import neo_to_py

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found."}},
    )


@router.get(
    "/",
    summary="Get info on available models",
    dependencies=[Depends(paging_params)],
)
def models_get(request: Request) -> List[BaseModel]:
    stmt = " ".join(
        ['MATCH (n0:model) RETURN n0 as model',
         f"SKIP {request.state.skip} " if request.state.skip else "",
         f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    for row in rows:
        ret.append(neo_to_py(row['model']))

    return sorted(ret, key=lambda x: (x.name or "", x.version is None, x.version or ""))


@router.get(
    "/count",
    summary="Get number of available models"
)
def models_count_get(request: Request) -> int:
    stmt = 'MATCH (n0:model) RETURN count(n0) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret[0]['count']
