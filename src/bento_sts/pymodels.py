from __future__ import annotations
from typing import List, Literal
from pydantic_core import Url
from pydantic import BaseModel


class Entity(BaseModel):
    type: str
    handle: str | None = None
    version: str | None = None
    nanoid: str


class Model(Entity):
    type: Literal['Model'] = 'Model'
    name: str | None = None
    repo: Url | None = None
    is_latest_version: bool
    nanoid: str | None = None


class Node(Entity):
    type: Literal['Node'] = 'Node'
    model: str


class Property(Entity):
    type: Literal['Property'] = 'Property'
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
    type: Literal['Term'] = 'Term'
    value: str
    origin_name: str
    handle: str | None = None
    origin_version: str | None = None
    origin_id: str | None = None
    nanoid: str


class Tag(BaseModel):
    type: Literal['Tag'] = 'Tag'
    key: str
    value: str
    nanoid: str


class Relationship(Entity):
    type: Literal['Relationship'] = 'Relationship'
    model: str


class Concept(Entity):
    type: Literal['Concept'] = 'Concept'


class ValueSet(Entity):
    type: Literal['ValueSet'] = 'ValueSet'


class Predicate(Entity):
    type: Literal['Predicate'] = 'Predicate'


class CDE(BaseModel):
    type: Literal['CDE'] = 'CDE'
    CDECode: str
    CDEVersion: str | None = None
    CDEFullName: str


class CDEWithPermissibleValues(CDE):
    permissibleValues: List[str]


class CDEWithModelInfo(CDE):
    models: List[Property]
