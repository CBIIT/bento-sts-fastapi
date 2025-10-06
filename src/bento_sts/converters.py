from logging import getLogger
from neo4j.graph import Node as neoNode
from pydantic_core import BaseModel
from .pymodels import (
    Model, Node, Property,
    Relationship, Concept, ValueSet,
    Term, Tag, CDE,
)

logger = getLogger()


def neo_to_py(neo_node: neoNode) -> BaseModel:
    returnCls = None
    if 'node' in neo_node.labels:
        returnCls = Node
    elif 'property' in neo_node.labels:
        returnCls = Property
    elif 'relationship' in neo_node.labels:
        returnCls = Relationship
    elif 'concept' in neo_node.labels:
        returnCls = Concept
    elif 'value_set' in neo_node.labels:
        returnCls = ValueSet
    elif 'model' in neo_node.labels:
        returnCls = Model
    elif 'tag' in neo_node.labels:
        returnCls = Tag
    elif 'term' in neo_node.labels:
        returnCls = Term
    else:
        logger.warning(
            f"Neo4j node with labels {neo_node.labels} cannot be converted "
            "to a current Pydantic model")
        return
    return returnCls(**dict(neo_node.items()))


def neo_to_cde(neo_node: neoNode):
    if 'term' not in neo_node.labels:
        logger.warning(
            "Can only convert a term node to a CDE object; "
            f"got Neo4j node with labels {neo_node.labels}"
        )
        return
    props = dict(neo_node.items())
    return CDE(
        CDECode=props['origin_id'],
        CDEVersion=props['origin_version'],
        CDEFullName=props['value'],
    )
