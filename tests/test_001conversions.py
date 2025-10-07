import pytest
from bento_sts.converters import neo_to_py, neo_to_cde
from bento_sts.pymodels import (
    Model, Node, Property,
    Relationship, Concept, ValueSet,
    Term, Tag, CDE,
)


def test_Node_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:node) return n limit 1")
    node = neo_to_py(result[0]['n'])
    assert isinstance(node, Node)


def test_Model_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:model) return n limit 1")
    model = neo_to_py(result[0]['n'])
    assert isinstance(model, Model)


def test_Property_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:property) return n limit 1")
    prop = neo_to_py(result[0]['n'])
    assert isinstance(prop, Property)


def test_Relationship_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:relationship) return n limit 1")
    reln = neo_to_py(result[0]['n'])
    assert isinstance(reln, Relationship)


def test_Concept_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:concept) return n limit 1")
    concept = neo_to_py(result[0]['n'])
    assert isinstance(concept, Concept)


def test_ValueSet_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:value_set) return n limit 1")
    vs = neo_to_py(result[0]['n'])
    assert isinstance(vs, ValueSet)


def test_Term_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:term) return n limit 1")
    term = neo_to_py(result[0]['n'])
    assert isinstance(term, Term)


def test_Tag_to_py(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:tag) return n limit 1")
    tag = neo_to_py(result[0]['n'])
    assert isinstance(tag, Tag)


def test_Term_to_pycde(test_sts_mdb):
    result = test_sts_mdb.get_with_statement("match (n:term {origin_name:'caDSR'}) return n limit 1")
    cde = neo_to_cde(result[0]['n'])
    assert isinstance(cde, CDE)
