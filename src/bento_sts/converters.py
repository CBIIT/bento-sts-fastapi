from .pymodels import (
    Model, Node, Property,
    Term, Tag, CDE,
)


def toModel(data: dict) -> Model:
    return Model(
        handle=data.get('handle'),
        version=data.get('version'),
        is_latest_version=data.get('is_latest_version') or False,
        nanoid=data.get('nanoid'),
    )


def toNode(data: dict) -> Node:
    return Node(
        handle=data.get('handle'),
        model=data.get('model'),
        version=data.get('version'),
        nanoid=data.get('nanoid'),
    )


def toProperty(data: dict) -> Property:
    return Property(
        handle=data.get('handle'),
        model=data.get('model'),
        version=data.get('version'),
        is_key=data.get('is_key'),
        is_strict=data.get('is_strict'),
        is_nullable=data.get('is_nullable'),
        is_required=data.get('is_required'),
        value_domain=data.get('value_domain'),
        item_domain=data.get('item_domain'),
        units=data.get('units'),
        pattern=data.get('units'),
        nanoid=data.get('nanoid'),
    )


def toTerm(data: dict) -> Term:
    return Term(
        handle=data.get('handle'),
        value=data.get('value'),
        origin_name=data.get('origin_name'),
        origin_version=data.get('origin_version'),
        origin_id=data.get('origin_id'),
        nanoid=data.get('nanoid'),
    )


def toTag(data: dict) -> Tag:
    return Tag(
        key=data.get('key'),
        value=data.get('value'),
        nanoid=data.get('nanoid'),
    )


def toCDE(term_data: dict) -> CDE:
    return CDE(
        CDECode=term_data.get('origin_id'),
        CDEVersion=term_data.get('origin_version'),
        CDEFullName=term_data.get('value'),
    )
