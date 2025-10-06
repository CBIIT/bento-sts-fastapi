from __future__ import annotations
from typing import List, Literal
from pydantic_core import Url
from pydantic import BaseModel


class Entity(BaseModel):
    _type: str
    handle: str | None = None
    version: str | None = None
    nanoid: str


class Model(Entity):
    _type: Literal['Model'] = 'Model'
    name: str | None = None
    repo: Url | None = None
    is_latest_version: bool


class Node(Entity):
    _type: Literal['Node'] = 'Node'
    model: str


class Property(Entity):
    _type: Literal['Property'] = 'Property'
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
    _type: Literal['Term'] = 'Term'
    value: str
    origin_name: str
    handle: str | None = None
    origin_version: str | None = None
    origin_id: str | None = None


class Tag(BaseModel):
    _type: Literal['Tag'] = 'Tag'
    key: str
    value: str
    nanoid: str


class Relationship(Entity):
    _type: Literal['Relationship'] = 'Relationship'


class Concept(Entity):
    _type: Literal['Concept'] = 'Concept'


class ValueSet(Entity):
    _type: Literal['ValueSet'] = 'ValueSet'


class Predicate(Entity):
    _type: Literal['Predicate'] = 'Predicate'


class CDE(BaseModel):
    _type: Literal['CDE'] = 'CDE'
    CDECode: str
    CDEVersion: str
    CDEFullName: str


class CDEWithPermissibleValues(CDE):
    permissibleValues: List[str]


class CDEWithModelInfo(CDE):
    models: List[Property]
