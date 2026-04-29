from fastapi import APIRouter
from ..dependencies import mdb

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/cache/clear",
    summary="Clear the in-process query cache.",
    responses={
        200: {"description": "Cache cleared successfully."},
    },
)
def cache_clear():
    """Invalidate all cached Neo4j query results immediately.

    Call this after a daily MDB data update to ensure subsequent requests
    reflect the latest data rather than serving stale cached results.
    """
    mdb.clear_cache()
    return {"status": "cache cleared"}
