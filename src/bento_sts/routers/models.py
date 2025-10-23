import re
import semver
from fastapi import APIRouter, Depends, Request
from typing import List
from functools import cmp_to_key
from ..dependencies import paging_params
from ..converters import neo_to_py
from ..pymodels import Model

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found."}},
    )


def extract_semver_base(version_str):
    """Extract X.Y.Z from version string: "1.6.0-9351eb2" → "1.6.0", "1.9" → "1.9.0" """
    if not version_str:
        return None
    match = re.match(r'(\d+\.\d+(?:\.\d+)?)(?:-(.+))?', version_str)
    if match:
        base = match.group(1)
        # Pad to X.Y.Z format
        parts = base.split('.')
        while len(parts) < 3:
            parts.append('0')
        return '.'.join(parts)
    return None

@router.get(
    "/",
    summary="Get info on available models",
    dependencies=[Depends(paging_params)],
)
def models_get(request: Request) -> List[Model]:
    def cmp_model(m: Model, n: Model):
        if (m.name == n.name):
            m_base = extract_semver_base(m.version)
            n_base = extract_semver_base(n.version)
            # Only call semver.compare if both bases are valid
            if m_base and n_base:
                res = semver.compare(m_base, n_base)
                if res != 0:
                    return res
                # If bases are equal, compare full strings (for prerelease)
                return -1 if m.version < n.version else (0 if m.version == n.version else 1)
            # If either base is None, compare as strings
            return -1 if m.version < n.version else (0 if m.version == n.version else 1)
        else:
            return -1 if m.name < n.name else 1

    stmt = " ".join(
        ['MATCH (n0:model) RETURN n0 as model',
         f"SKIP {request.state.skip} " if request.state.skip else "",
         f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = []
    rows = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    for row in rows:
        ret.append(neo_to_py(row['model']))
    return sorted(ret, key=cmp_to_key(cmp_model))


@router.get(
    "/count",
    summary="Get number of available models"
)
def models_count_get(request: Request) -> int:
    stmt = 'MATCH (n0:model) RETURN count(n0) as count'
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret[0]['count']
