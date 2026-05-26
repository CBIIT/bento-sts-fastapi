from logging import getLogger
from fastapi import Request
from pydantic import Field
from typing import Annotated
from .mdb import MDBReader


logger = getLogger(__name__)
mdb = MDBReader()


def make_paging_params(default_limit: int = 0):
    def paging_params(
        request: Request,
        skip: Annotated[int, Field(ge=0)] = 0,
        limit: Annotated[int, Field(ge=0)] = default_limit,
    ):
        # treat limit=0 as "use default_limit" when a default is set,
        effective_limit = limit if limit > 0 else default_limit
        request.state.skip = skip
        request.state.limit = effective_limit
        return {"skip": skip, "limit": effective_limit}
    return paging_params


paging_params = make_paging_params(default_limit=0)
paging_params_tags = make_paging_params(default_limit=100)


def get_mdb(request: Request):
    request.state.mdb = mdb
    return mdb
