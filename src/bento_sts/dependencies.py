from logging import getLogger
from fastapi import Request
from .mdb import MDBReader
from pdb import set_trace

logger = getLogger()
mdb = MDBReader()


def paging_params(request: Request, skip: int = 0, limit: int = 0):
    request.state.skip = skip
    request.state.limit = limit
    return {"skip": skip, "limit": limit}


def get_mdb(request: Request):
    request.state.mdb = mdb
    return mdb
