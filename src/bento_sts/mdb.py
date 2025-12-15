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
from pdb import set_trace

# Decorator functions to produce executed transactions based on an
# underlying query/param function:

logger = logging.getLogger()
load_dotenv()

def read_txn(func):
    """
    Decorates a query function to run a read transaction based on
    its query.
    Query function should return a tuple (qry_string, param_dict).
    Returns list of driver Records.
    If a query returns 0 records, raise an HTTPException
    """

    @wraps(func)
    def rd(self, *args, **kwargs):
        def txn_q(tx):
            (qry, parms) = func(self, *args, **kwargs)
            result = tx.run(qry, parameters=parms)
            return [rec for rec in result]
        with self.driver.session() as session:
            result = session.execute_read(txn_q)
            if len(result) == 0:
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
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        except Exception as e:
            logger.warning(f"MDB not connected: {e}")

    def close(self):
        self.driver.close()
        
    @read_txn
    def get_with_statement(self, qry: str, parms: dict = {}):
        """Run an arbitrary read statement and return data."""
        return (qry, parms)
