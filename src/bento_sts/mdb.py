"""
bento_sts.mdb

Class to instantiate a connection and query an MDB in a Neo4j database.
"""

import os
import logging
from functools import wraps
from neo4j import GraphDatabase
from dotenv import load_dotenv
from fastapi import HTTPException
from cachetools import TTLCache

# Decorator functions to produce executed transactions based on an
# underlying query/param function:

logger = logging.getLogger(__name__)
# Uvicorn already attaches handlers to uvicorn.error; avoids extra app-level logging setup.
_cache_log = logging.getLogger("uvicorn.error")
load_dotenv()

def read_txn(func):
    """
    Decorates a query function to run a read transaction based on
    its query.
    Query function should return a tuple (qry_string, param_dict).
    Returns list of driver Records.
    If a query returns 0 records, raise an HTTPException (unless raise_on_empty=False)
    """

    @wraps(func)
    def rd(self, *args, **kwargs):
        # Extract raise_on_empty from kwargs, default to True
        raise_on_empty = kwargs.pop('raise_on_empty', True)
        
        def txn_q(tx):
            (qry, parms) = func(self, *args, **kwargs)
            result = tx.run(qry, parameters=parms)
            return [rec for rec in result]
        with self.driver.session() as session:
            result = session.execute_read(txn_q)
            if len(result) == 0 and raise_on_empty:
                raise HTTPException(status_code=404,
                                    detail="Not found.")
            return result
    return rd


class MDBReader(object):
    def __init__(
        self,
        uri: str = os.environ.get("NEO4J_MDB_URI"),
        user: str = os.environ.get("NEO4J_MDB_USER"),
        password: str = os.environ.get("NEO4J_MDB_PASS")
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self._cache = TTLCache(
            maxsize=int(os.environ.get("STS_CACHE_MAXSIZE", 4096)),
            ttl=int(os.environ.get("STS_CACHE_TTL", 172800)),
        )
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        except Exception as e:
            logger.warning(f"MDB not connected: {e}")

    def close(self):
        self.driver.close()
        
    @read_txn
    def _execute_query(self, qry: str, parms: dict = {}):
        return (qry, parms)

    def get_with_statement(self, qry: str, parms: dict = {}, raise_on_empty: bool = True):
        """Run an arbitrary read statement, returning cached results when available.

        Results are cached for 24 hours (TTL=86400s). Cache misses execute the query
        against Neo4j. HTTPException(404) responses are never cached.

        Args:
            qry: Cypher query string
            parms: Query parameters
            raise_on_empty: If True (default), raises HTTPException(404) when no results found.
                          If False, returns empty list when no results found.
        """
        key = (qry, tuple(sorted(parms.items())), raise_on_empty)
        if key in self._cache:
            preview = qry.split("\n")[0].strip()[:60]
            parms_str = f" parms={parms}" if parms else ""
            _cache_log.info("mdb cache HIT  [size=%d] query='%s'%s", len(self._cache), preview, parms_str)
            return self._cache[key]
        result = self._execute_query(qry, parms, raise_on_empty=raise_on_empty)
        self._cache[key] = result
        return result

    def clear_cache(self):
        """Invalidate all cached query results."""
        count = len(self._cache)
        self._cache.clear()
        _cache_log.info("mdb cache cleared (%d entries evicted)", count)