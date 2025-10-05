from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic_core import Url
from pydantic import BaseModel, Field


class Entity(BaseModel):
    handle: str
    version: str
    nanoid: str

    
class Model(Entity):
    name: str | None = None
    repo: Url | None = None

    
class Node(Entity):
    model: str

    
class Property(Entity):
    model: str
    is_required: bool | None = None
    value_domain: str
    units: str | None = None
    pattern: str | None = None


class Term(BaseModel):
    value: str
    origin_name: str
    nanoid: str
    handle: str | None = None
    origin_version: str | None = None
    origin_id: str | None = None


class Tag(BaseModel):
    key: str
    value: str
    nanoid: str

    
class CDE(BaseModel):
    CDECode: str
    CDEVersion: str
    CDEFullName: str


class CDEWithPermissibleValues(CDE):
    permissibleValues: List[str]


class CDEWithModelInfo(CDE):
    models: List[Property]

