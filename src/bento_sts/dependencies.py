import os
from logging import getLogger
from fastapi import Request
from bento_meta.mdb import SearchableMDB
from dotenv import load_dotenv

load_dotenv()
logger = getLogger()

mdb = SearchableMDB(
    os.getenv("NEO4J_MDB_URI"),
    os.getenv("NEO4J_MDB_USER"),
    os.getenv("NEO4J_MDB_PASS"))


def paging_params(request: Request, skip: int = 0, limit: int = 0):
    request.state.skip = skip
    request.state.limit = limit
    return {"skip": skip, "limit": limit}


def get_mdb(request: Request):
    request.state.mdb = mdb
    return mdb
