from logging import getLogger
from neo4j.graph import Node as neoNode
from pydantic import BaseModel
from .pymodels import (
    Model, Node, Property,
    Relationship, Concept, ValueSet, Origin,
    Term, Tag, CDE,
)
from pdb import set_trace
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
    elif 'origin' in neo_node.labels:
        returnCls = Origin
    elif 'model' in neo_node.labels:
        returnCls = Model
    elif 'tag' in neo_node.labels:
        returnCls = Tag
    elif 'term' in neo_node.labels:
        returnCls = Term
    else:
        logger.error(
            f"Neo4j node with labels {neo_node.labels} cannot be converted "
            "to a current Pydantic model")
        return
    if (returnCls is not None):
        return returnCls(**dict(neo_node.items()))


def neo_to_cde(neo_node: neoNode):
    if 'term' not in neo_node.labels:
        logger.warning(
            "Can only convert a term node to a CDE object; "
            f"got Neo4j node with labels {neo_node.labels}"
        )
        return
    props = dict(neo_node.items())
    vers = props.get('origin_version')
    if not vers:
        logger.warning(f"caDSR term with nanoid '{props['nanoid']}' is missing 'origin_version'")
    return CDE(
        CDECode=props['origin_id'],
        CDEVersion=vers,
        CDEFullName=props['value'],
    )
