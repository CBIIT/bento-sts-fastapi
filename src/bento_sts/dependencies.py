from logging import getLogger
from fastapi import Request, Query
from pydantic import Field
from typing import Annotated
from .mdb import MDBReader
from pdb import set_trace

logger = getLogger()
mdb = MDBReader()


def paging_params(
    request: Request,
    skip: Annotated[int, Field(ge=0)] = 0,
    limit: Annotated[int, Field(ge=0)] = 0
):
    request.state.skip = skip
    request.state.limit = limit
    return {"skip": skip, "limit": limit}


def get_mdb(request: Request):
    request.state.mdb = mdb
    return mdb
