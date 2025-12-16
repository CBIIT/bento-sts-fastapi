import semver
from fastapi import APIRouter, Depends, Request
from typing import List
from functools import cmp_to_key
from ..dependencies import paging_params
from ..converters import neo_to_py
from ..pymodels import Model
from ..utility.version_utils import model_version_compare

router = APIRouter(
    prefix="/models",
    tags=["models"],
    )


@router.get(
    "/",
    summary="Get info on available models",
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (skip or limit?)"},
    },
)
def models_get(request: Request) -> List[Model]:
    rows = request.state.mdb.get_with_statement(
        'MATCH (n0:model) RETURN n0 as model',
        {}
    )
    sorted_models = sorted(
        (neo_to_py(row['model']) for row in rows),
        key=cmp_to_key(model_version_compare)
    )

    skip = max(request.state.skip or 0, 0)
    limit = request.state.limit
    limit = limit if limit and limit > 0 else None

    return (sorted_models[skip:skip + limit]
            if limit is not None else sorted_models[skip:])


@router.get(
    "/count",
    summary="Get number of available models",
    responses={
        200: {"description": "Successful Response"},
    },
)
def models_count_get(request: Request) -> int:
    stmt = 'MATCH (n0:model) RETURN count(n0) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret[0]['count']
