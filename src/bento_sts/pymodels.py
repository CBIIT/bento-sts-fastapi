from __future__ import annotations
from typing import List
from pydantic_core import Url
from pydantic import BaseModel


class Entity(BaseModel):
    handle: str | None = None
    version: str | None = None
    nanoid: str


class Model(Entity):
    name: str | None = None
    repo: Url | None = None
    is_latest_version: bool


class Node(Entity):
    model: str


class Property(Entity):
    model: str
    is_key: bool | None = None
    is_strict: bool | None = None
    is_nullable: bool | None = None
    is_required: bool | None = None
    value_domain: str
    item_domain: str | None = None
    units: str | None = None
    pattern: str | None = None


class Term(BaseModel):
    value: str
    origin_name: str
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
