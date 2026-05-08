from fastapi import APIRouter, Depends, Request
from typing import List
from ..dependencies import paging_params
from ..pymodels import Term
from ..converters import neo_to_py

router = APIRouter(
    prefix="/edp",
    tags=["edp"],
    dependencies=[Depends(paging_params)],
    )

@router.get(
    "/{originName}/{originId}/{originVersion}/terms",
    summary="Get PV terms for a given EDP origin, id and version.",
    response_model=List[Term],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (origin, id, version, skip, or limit?)"},
    },
)
def edp_pvs_by_origin_id_version_get(
    request: Request, originName: str, originId: str, originVersion: str
    ):
    NULL_CDE_ID = '16476366|1'
    stmt = " ".join([
        "MATCH (t:term {origin_name: $origin_name, origin_id: $origin_id,",
        "               origin_version: $origin_version})",
        "-[:specifies_value_set]->(v:value_set)-[:has_term]->(t:term)",
        "return t",
        f"SKIP {request.state.skip} " if request.state.skip else "",
        f"LIMIT {request.state.limit}" if request.state.limit else ""])
    rows = request.state.mdb.get_with_statement(
        stmt,
        {"origin_name": originName, "origin_id": originId, "origin_version": originVersion}
    )
    ret = []
    for row in rows:
        ret.append(neo_to_py(row['t']))
    return ret
