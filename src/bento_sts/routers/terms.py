from fastapi import APIRouter, Depends, Request
from typing import List
from functools import cmp_to_key
from ..dependencies import paging_params
from ..pymodels import CDEPermissibleValuesModel, CDEPermissibleValues
from ..converters import neo_to_py
from ..utility.version_utils import model_version_compare

router = APIRouter(
    prefix="/terms",
    tags=["terms"],
    dependencies=[Depends(paging_params)],
    )

@router.get(
    "/model-pvs/{model}/{property:path}",
    summary="Get Permissible Values and Synonyms for a model, optionally filtered by property and version.",
    response_model=List[CDEPermissibleValuesModel],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (model or property or version or skip or limit?)"},
    },
)
def pvs_synonyms_model_version_get(request: Request, model: str, property: str = "", version: str | None = None):
    # If version is not provided, get the latest version for the model
    if version is None or version.strip() == "":
        # find a model with is_latest_version
        stmt = "MATCH (m:model {handle:$p0, is_latest_version:true}) RETURN m AS model"
        result = request.state.mdb.get_with_statement(stmt, {"p0": model}, raise_on_empty=False)
        
        if result:
            # Found models with is_latest_version
            models = [neo_to_py(row['model']) for row in result]
            version = sorted(models, key=cmp_to_key(model_version_compare))[-1].version
        else:
            # get all versions and pick the latest version
            stmt = "MATCH (m:model {handle:$p0}) RETURN m AS model"
            result = request.state.mdb.get_with_statement(stmt, {"p0": model})
            models = [neo_to_py(row['model']) for row in result]
            version = sorted(models, key=cmp_to_key(model_version_compare))[-1].version
    
    # Clean property: remove quotes and whitespace; Swagger doc requires to reqeust a value input.
    property = property.strip().strip('"').strip("'").strip()
    
    # Build parameters and query based on whether property is specified
    has_property = property and property != ""
    params = {"p0": model, "p1": version, "p3": request.state.skip, "p4": request.state.limit} | ({"p2": property} if has_property else {})
    
    stmt = """
    MATCH (n0:node {model:$p0})-[r0:has_property]->(n1:property)
    WITH n1 AS prop
    WHERE n0.version = $p1""" + (" AND prop.handle = $p2" if has_property else "") + """
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
    [pv_item IN collect({value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}) WHERE pv_item.value IS NOT NULL] AS formatted_pvs
    RETURN DISTINCT $p0 AS model, $p1 AS version,
      prop.handle AS property,
      CASE 
        WHEN $p4 > 0 THEN formatted_pvs[$p3..($p3 + $p4)]
        WHEN $p3 > 0 THEN formatted_pvs[$p3..]
        ELSE formatted_pvs
      END AS permissibleValues
"""
    ret = request.state.mdb.get_with_statement(
        stmt,
        params
    )
    return [record.data() if hasattr(record, 'data') else dict(record.items()) for record in ret]
    

@router.get(
    "/cde-pvs/{id}/{version}/pvs",
    summary="Get PVs for a given CDE id and version.",
    response_model=List[CDEPermissibleValues],
    responses={
        200: {"description": "Successful Response"},
        404: {"description": "Not found."},
        422: {"description": "Bad parameters (id or version or skip or limit?)"},
    },
)
def cde_pvs_by_id_with_version_get(request: Request, id: str, version: str):
    stmt = """
    MATCH (n0:term {origin_id: $p0 })
      WHERE $p1 = "none" OR n0.origin_version = $p1
    OPTIONAL MATCH (vs:value_set)-[:has_term]->(pv:term)
      WHERE vs.handle = $p0 + '|' + coalesce(n0.origin_version, "")
    WITH n0, vs.url as value_set_url, COLLECT(pv) as pvs WITH n0,
      value_set_url, pvs,
      CASE WHEN size(pvs) > 0 THEN pvs ELSE [null] END as pvs_to_process
    UNWIND pvs_to_process AS pv
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {origin_name: "NCIt"}), (c_cadsr)-[:has_tag]->(:tag {key: "mapping_source", value: "caDSR"})
      WHERE pv IS NOT NULL
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term), (c_ncim)-[:has_tag]->(:tag {key: "mapping_source", value: "NCIm"})
      WHERE pv IS NOT NULL AND pv <> syn and pv.value <> syn.value
    WITH n0, value_set_url, pvs,
      CASE WHEN pv IS NULL THEN null ELSE pv.value END as pv_val,
      CASE WHEN pv IS NULL THEN null ELSE ncit_term.origin_id END AS ncit_oid,
      CASE WHEN pv IS NULL THEN null ELSE ncit_term.value END AS ncit_value,
      collect(DISTINCT syn.value) AS distinct_syn_vals
    WITH n0, value_set_url, pvs,
      CASE WHEN pv_val IS NULL THEN [] ELSE collect({value: pv_val, synonyms: CASE WHEN ncit_value IS NOT NULL THEN distinct_syn_vals + [ncit_value] ELSE distinct_syn_vals END, ncit_concept_code: ncit_oid}) END AS permissibleValues
    WITH n0.origin_id AS CDECode, n0.origin_version AS CDEVersion,
      n0.value AS CDEFullName, 
      CASE 
        WHEN $p3 > 0 THEN permissibleValues[$p2..($p2 + $p3)]
        WHEN $p2 > 0 THEN permissibleValues[$p2..]
        ELSE permissibleValues
      END AS permissibleValues
    RETURN CDECode, CDEVersion, CDEFullName, permissibleValues"""
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": id, "p1": version, "p2": request.state.skip, "p3": request.state.limit}
    )
    return [record.data() if hasattr(record, 'data') else dict(record.items()) for record in ret]
