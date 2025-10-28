from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params
from ..pymodels import Term, CDE
from ..converters import neo_to_py, neo_to_cde

router = APIRouter(
    prefix="/terms",
    tags=["terms"],
    dependencies=[Depends(paging_params)],
    responses={404: {"description": "Not found."}},
    )

@router.get(
    "/model-pvs/{model}/{version}/pvs",
    summary="Get Permissible Values and Synonyms for a specified model and version."
)
def pvs_synonyms_model_version_get(request: Request, model: str, version: str):
    stmt = """
    MATCH (n0:node {model:$p0,version:$p1})-[r0:has_property]->(n1:property)
    WITH collect(n1) AS props UNWIND props AS prop
    OPTIONAL MATCH (prop)-[:has_concept]->(c:concept)<-[:represents]-(cde:term)
      WHERE toLower(cde.origin_name) CONTAINS "cadsr"
    OPTIONAL MATCH (prop)-[:has_value_set]->(:value_set)-[:has_term]->(t:term)
    WITH prop, cde.origin_id AS CDECode, cde.origin_version AS CDEVersion,
      cde.value AS CDEFullName,
      cde.origin_id + "|" + COALESCE(cde.origin_version, "") AS cde_hdl,
      collect(t) AS model_pvs,
      CASE WHEN cde IS NOT NULL THEN true ELSE false END AS has_cde
    OPTIONAL MATCH (v:value_set {handle: cde_hdl})-[:has_term]->(cde_pv:term)
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, has_cde,
      collect(cde_pv) AS cde_pvs WITH prop, CDECode, CDEVersion, CDEFullName,
      model_pvs, has_cde, cde_pvs,
      CASE WHEN has_cde AND size(cde_pvs) > 0 AND
        NONE(p in cde_pvs WHERE p.value =~ "https?://.*")
        THEN cde_pvs WHEN has_cde and size(cde_pvs) > 0 AND
        ANY(p in cde_pvs WHERE p.value =~ "https?://.*") AND
        size(model_pvs) > 0
        THEN model_pvs WHEN NOT has_cde AND size(model_pvs) > 0
        THEN model_pvs ELSE [null] END AS pvs
    UNWIND pvs AS pv
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {origin_name: "NCIt"}), (c_cadsr)-[:has_tag]->(:tag {key: "mapping_source", value: "caDSR"})
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term), (c_ncim)-[:has_tag]->(:tag {key: "mapping_source", value: "NCIm"})
      WHERE pv <> syn and pv.value <> syn.value
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, pv.value AS pv_val,
      ncit_term.origin_id AS ncit_oid, ncit_term.value AS ncit_value,
      collect(DISTINCT syn.value) AS distinct_syn_vals
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, pv_val, ncit_oid,
      CASE WHEN ncit_value IS NOT NULL
        THEN distinct_syn_vals + [ncit_value]
        ELSE distinct_syn_vals END AS syn_vals
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs,
    collect({value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}) AS formatted_pvs
    RETURN $p0 AS dataCommons, $p1 AS version,
      prop AS property, CDECode, CDEVersion, CDEFullName,
      formatted_pvs AS permissibleValues
"""
    stmt = " ".join([stmt, 
                     f"SKIP {request.state.skip} " if request.state.skip else "",
                     f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": model, "p1": version}
    )
    return ret
    

@router.get(
    "/cde-pvs/{prop}/pvs",
    summary="Get PVs for a given handle property."
)
def cde_pvs_by_property_get(request: Request, prop: str):
    stmt = """
    MATCH (p:property {handle: $p0})
    WITH p
    OPTIONAL MATCH (p)-[:has_concept]->(:concept)<-[:represents]-(cde:term)
      WHERE toLower(cde.origin_name) CONTAINS 'cadsr'
    OPTIONAL MATCH (p)-[:has_tag]->(use_null_tag:tag {key: "useNullCDE"})
    WITH DISTINCT p, cde,
      cde.origin_id + "|" + COALESCE(cde.origin_version, "") AS cde_hdl,
      CASE WHEN cde IS NOT NULL THEN true ELSE false END AS has_cde,
      ANY(ut IN COLLECT(use_null_tag) WHERE ut.value IN ["Yes", "True"] OR ut.value = true) AS should_use_null_cde
    WHERE cde IS NOT NULL
    OPTIONAL MATCH (n0:node)-[:has_property]->(p)
    WITH p, cde, cde_hdl, has_cde, should_use_null_cde,
      COLLECT(DISTINCT {model: n0.model, version: n0.version}) AS model_versions
    WHERE SIZE(model_versions) > 0
    UNWIND model_versions AS mv
    OPTIONAL MATCH (p)-[:has_value_set]->(:value_set)-[:has_term]->(model_pv:term)
    WITH p, cde, cde_hdl, has_cde, should_use_null_cde, mv,
      COLLECT(DISTINCT model_pv) AS model_pvs
    OPTIONAL MATCH (v:value_set {handle: cde_hdl})-[:has_term]->(cde_pv:term)
    WITH p, cde, has_cde, should_use_null_cde, mv, model_pvs,
      [pv IN COLLECT(DISTINCT cde_pv) WHERE pv IS NOT NULL] AS cde_pvs
    OPTIONAL MATCH (null_vs:value_set {handle: '16476366|1'})-[:has_term]->(null_pv:term)
    WITH p, cde, has_cde, should_use_null_cde, mv, model_pvs, cde_pvs,
      CASE WHEN should_use_null_cde THEN COLLECT(DISTINCT null_pv) ELSE [] END AS null_pvs
    WITH p, cde, has_cde, should_use_null_cde, mv, model_pvs, cde_pvs, null_pvs,
      CASE 
        WHEN has_cde AND SIZE(cde_pvs) > 0 AND NONE(pv in cde_pvs WHERE pv.value =~ 'https?://.*')
          THEN cde_pvs + null_pvs
        WHEN has_cde AND SIZE(cde_pvs) > 0 AND ANY(pv in cde_pvs WHERE pv.value =~ 'https?://.*') AND SIZE(model_pvs) > 0
          THEN model_pvs + null_pvs
        WHEN NOT has_cde AND SIZE(model_pvs) > 0
          THEN model_pvs + null_pvs
        WHEN SIZE(null_pvs) > 0
          THEN null_pvs
        ELSE [null]
      END AS pvs
    WHERE SIZE(pvs) > 0
    UNWIND pvs AS pv
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {origin_name: 'NCIt'}),
      (c_cadsr)-[:has_tag]->(:tag {key: "mapping_source", value: "caDSR"})
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term),
      (c_ncim)-[:has_tag]->(:tag {key: "mapping_source", value: "NCIm"})
    WHERE pv IS NOT NULL AND (syn IS NULL OR (pv <> syn AND pv.value <> syn.value))
    WITH cde, p, mv, pv, pv.value as pv_val, 
      ncit_term.origin_id AS ncit_oid,
      ncit_term.value AS ncit_value,
      COLLECT(DISTINCT syn.value) AS distinct_syn_vals
    WITH cde, p, mv, pv_val, ncit_oid,
      CASE WHEN ncit_value IS NOT NULL THEN distinct_syn_vals + [ncit_value] ELSE distinct_syn_vals END AS syn_vals
    WITH cde, p, mv,
        CASE WHEN pv_val IS NOT NULL THEN COLLECT(DISTINCT {value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}) ELSE [] END AS formatted_pvs
    RETURN DISTINCT
      cde.origin_id AS CDECode,
      cde.origin_version AS CDEVersion,
      cde.value AS CDEFullName,
      mv.model AS dataCommons,
      mv.version AS version,
      formatted_pvs AS permissibleValues,
      p.handle AS property
    """
    stmt = " ".join([stmt,
                     f"SKIP {request.state.skip} " if request.state.skip else "",
                     f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": prop}
    )
    return ret
    

@router.get(
    "/all-pvs",
    summary="Get all PVs and synonyms for all models and CDEs"
)
def all_pvs_get(request: Request):
    stmt = """
    MATCH (cde:term)
      WHERE toLower(cde.origin_name) CONTAINS "cadsr"
    WITH cde
    MATCH (ent)-[:has_property]->(p:property)-[:has_concept]->(:concept)<-[:represents]-(cde)
      WHERE p.model IS NOT NULL AND p.version IS NOT NULL
    WITH cde,
      collect(DISTINCT {model: p.model, version: p.version, property: ent.handle + "." + p.handle}) AS models
    WITH cde, models, cde.origin_id + "|" + coalesce(cde.origin_version, "") AS cde_hdl
    OPTIONAL MATCH (prop:property)-[:has_concept]->(c:concept)<-[:represents]-(cde)
    OPTIONAL MATCH (prop)-[:has_value_set]->(:value_set)-[:has_term]->(model_pv:term)
    WITH cde, models, cde_hdl, collect(DISTINCT model_pv) AS model_pvs
    OPTIONAL MATCH (vs:value_set {handle: cde_hdl})-[:has_term]->(cde_pv:term)
    WITH cde, models, model_pvs, collect(DISTINCT cde_pv) AS cde_pvs
    WITH cde, models, model_pvs, cde_pvs,
      CASE WHEN size(cde_pvs) > 0 AND NONE(p in cde_pvs WHERE p.value =~ "https?://.*") THEN cde_pvs WHEN size(cde_pvs) > 0 AND ANY(p in cde_pvs WHERE p.value =~ "https?://.*") AND size(model_pvs) > 0 THEN model_pvs ELSE [null] END AS pvs
    WHERE size(pvs) > 0
    UNWIND pvs AS pv
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {origin_name: "NCIt"}), (c_cadsr)-[:has_tag]->(:tag {key: "mapping_source", value: "caDSR"})
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term), (c_ncim)-[:has_tag]->(:tag {key: "mapping_source", value: "NCIm"})
      WHERE pv IS NOT NULL AND pv <> syn AND pv.value <> syn.value
    WITH cde, pv, models, pv.value as pv_val, ncit_term.origin_id AS ncit_oid,
      ncit_term.value AS ncit_value,
      collect(DISTINCT syn.value) AS distinct_syn_vals WITH cde, models, pv_val,
      ncit_oid,
      CASE WHEN ncit_value IS NOT NULL THEN distinct_syn_vals + [ncit_value] ELSE distinct_syn_vals END AS syn_vals
    WITH cde, models,
      CASE WHEN pv_val IS NOT NULL THEN collect({value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}) ELSE [] END AS formatted_pvs
    RETURN cde.origin_id AS CDECode, cde.origin_version AS CDEVersion,
      cde.value AS CDEFullName, models, formatted_pvs AS permissibleValues"""

    stmt = " ". join([stmt,
                      f"SKIP {request.state.skip} " if request.state.skip else "",
                      f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {}
    )
    return ret
