from fastapi import APIRouter, Depends, Request
from typing import List
from ..dependencies import paging_params
from ..pymodels import Term
from ..converters import neo_to_py

router = APIRouter(
    prefix="/edps",
    tags=["edps"],
    dependencies=[Depends(paging_params)],
    )

@router.get(
    "/{originName}",
    summary="Get all extended definition property (EDP) defining terms, filtered by the origin (authority) of the terms (e.g., 'caDSR' for CDEs)",
    response_model=List[Term],
    dependencies=[Depends(paging_params)],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (skip or limit?)"},
    },
)
def edp_terms_get(request: Request, originName: str):
    stmt = " ".join([
        "MATCH (t:term {origin_name: $origin_name})-[:specifies_value_set]->(:value_set)",
        "RETURN t",
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])

    rows = request.state.mdb.get_with_statement(
        stmt,
        {"origin_name": originName}
    )
    ret = []
    for row in rows:
        ret.append(neo_to_py(row['t']))
    return ret
