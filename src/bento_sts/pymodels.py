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
    repository: Url | None = None
    is_latest_version: bool
    nanoid: str | None = None


class Node(Entity):
    type: Literal['Node'] = 'Node'
    model: str


class PropertyBase(BaseModel):
    """Base fields for Property-like objects"""
    model: str
    is_key: bool | None = None
    is_strict: bool | None = None
    is_nullable: bool | None = None
    is_required: str | bool | None = None
    value_domain: str
    item_domain: str | None = None


class Property(Entity, PropertyBase):
    type: Literal['Property'] = 'Property'
    units: str | None = None
    pattern: str | None = None
    desc: str | None = None


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
    value: str | bool
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


class PermissibleValue(BaseModel):
    value: str
    ncit_concept_code: str | None = None
    synonyms: List[str] | None = None


class CDEPermissibleValuesModel(BaseModel):
    model: str
    property: str
    version: str
    permissibleValues: List[PermissibleValue]


class CDEPermissibleValues(BaseModel):
    CDECode: str
    CDEFullName: str
    CDEVersion: str
    permissibleValues: List[PermissibleValue]


# Response models for specific endpoints
class PropertyResponse(Entity, PropertyBase):
    """Response model for /node/{nodeHandle}/properties endpoint"""
    type: Literal['Property'] = 'Property'
    desc: str | None = None
