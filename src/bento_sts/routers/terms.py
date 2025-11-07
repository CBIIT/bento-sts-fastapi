from fastapi import APIRouter, Depends, Request
from ..dependencies import paging_params

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
    OPTIONAL MATCH (prop)-[:has_tag]->(use_null_tag:tag {key: "useNullCDE"})
    WITH prop, cde, use_null_tag, cde.origin_id AS CDECode, cde.origin_version AS CDEVersion,
      cde.value AS CDEFullName,
      cde.origin_id + "|" + COALESCE(cde.origin_version, "") AS cde_hdl,
      CASE WHEN cde IS NOT NULL THEN true ELSE false END AS has_cde,
      ANY(ut IN COLLECT(use_null_tag) WHERE ut.value = true) AS should_use_null_cde
    OPTIONAL MATCH (prop)-[:has_value_set]->(:value_set)-[:has_term]->(model_pv:term)
    WITH prop, cde, CDECode, CDEVersion, CDEFullName, cde_hdl, has_cde, should_use_null_cde,
      collect(DISTINCT model_pv) AS model_pvs
    OPTIONAL MATCH (v:value_set {handle: cde_hdl})-[:has_term]->(cde_pv:term)
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, has_cde,
        collect(cde_pv) AS cde_pvs, should_use_null_cde
    OPTIONAL MATCH (null_vs:value_set {handle: "16476366|1"})-[:has_term]->(null_pv:term)
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, cde_pvs, has_cde, should_use_null_cde,
      CASE WHEN should_use_null_cde THEN COLLECT(DISTINCT null_pv) ELSE [] END AS null_pvs
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, cde_pvs, should_use_null_cde, null_pvs, has_cde,
      CASE 
        WHEN has_cde AND size(cde_pvs) > 0 AND NONE(p in cde_pvs WHERE p.value =~ "https?://.*")
            THEN cde_pvs + null_pvs 
        WHEN has_cde and size(cde_pvs) > 0 AND ANY(p in cde_pvs WHERE p.value =~ "https?://.*") AND size(model_pvs) > 0
            THEN model_pvs + null_pvs 
        WHEN NOT has_cde AND size(model_pvs) > 0
            THEN model_pvs + null_pvs 
        WHEN SIZE(null_pvs) > 0
            THEN null_pvs
        ELSE [null]
      END AS pvs
    WHERE size(pvs) > 0
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
      CASE WHEN pv_val IS NOT NULL THEN collect({value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}) ELSE [] END AS formatted_pvs
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
    "/cde-pvs/{id}/{version}/pvs",
    summary="Get PVs for a given CDE id and version."
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
    RETURN n0.origin_id AS CDECode, n0.origin_version AS CDEVersion,
      n0.value AS CDEFullName, permissibleValues"""
    stmt = " ".join([stmt,
                     f"SKIP {request.state.skip} " if request.state.skip else "",
                     f"LIMIT {request.state.limit}" if request.state.limit else ""])
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": id, "p1": version}
    )
    return ret
    

@router.get(
    "/all-pvs",
    summary="Get all PVs and synonyms for all models and CDEs"
)
def all_pvs_get(request: Request):
    NULL_CDE_ID = '16476366|1'
    stmt = f"""
    // start with all terms that are CDEs
    MATCH (cde:term)
      WHERE toLower(cde.origin_name) CONTAINS "cadsr"
    WITH cde
    // get all properties that are attached to each cde
    MATCH (ent)-[:has_property]->(p:property)-[:has_concept]->(:concept)<-[:represents]-(cde)
      WHERE p.model IS NOT NULL AND p.version IS NOT NULL
    OPTIONAL MATCH (p)-[:has_tag]->(use_null_tag:tag {{key: "useNullCDE"}})
    // get the model, version, and property handle of each property as a metadata dict for
    // each cde, and a flag that indicates if the null CDE should be included for that
    // model property
    WITH cde,
      COLLECT(DISTINCT {{
        model: p.model, 
        version: p.version, 
        property: ent.handle + "." + p.handle, 
        useNullCDE: COALESCE(use_null_tag.value, false)
      }}) AS models,
      ANY(ut IN COLLECT(use_null_tag) WHERE ut.value = true) AS should_use_null_cde
    WITH cde, models, should_use_null_cde, 
      cde.origin_id + "|" + COALESCE(cde.origin_version, "") AS cde_hdl
    // Get pvs in the MDF model for each property that has them
    OPTIONAL MATCH (prop:property)-[:has_concept]->(c:concept)<-[:represents]-(cde)
    OPTIONAL MATCH (prop)-[:has_value_set]->(:value_set)-[:has_term]->(model_pv:term)
    WITH cde, models, cde_hdl, collect(DISTINCT model_pv) AS model_pvs, should_use_null_cde
    // Now get the CDE's official pvs for each property that has them
    OPTIONAL MATCH (vs:value_set {{handle: cde_hdl}})-[:has_term]->(cde_pv:term)
    // at this point, for each CDE, we have the properties that are annotated with that
    // CDE, the PVs from the model files, and the PVs from the CDE for that property
    // (over all the models)
    WITH cde, models, should_use_null_cde, model_pvs, COLLECT(DISTINCT cde_pv) AS cde_pvs
    // Add the null CDE pvs if should_use_null_cde is set
    OPTIONAL MATCH (null_vs:value_set {{handle: '{NULL_CDE_ID}'}})-[:has_term]->(null_pv:term)
    WITH cde, models, model_pvs, cde_pvs, 
      CASE WHEN should_use_null_cde THEN COLLECT(DISTINCT null_pv) ELSE [] END AS null_pvs
    WITH cde, models,
      CASE
        // when there are cde_pvs for property and there are no URLs in the pv list
        // return cde and null pvs as the property's pv set:
        WHEN SIZE(cde_pvs) > 0 AND NONE(p IN cde_pvs WHERE p.value =~ "https?://.*") 
          THEN cde_pvs + null_pvs
        // when the "value set" of the CDE is just a url ("values by reference"), return
        // the model's defined enum as the pvs
        WHEN SIZE(cde_pvs) > 0 AND ANY(p IN cde_pvs WHERE p.value =~ "https?://.*") AND SIZE(model_pvs) > 0 
          THEN model_pvs + null_pvs
        // when there are no pvs defined in either location
        WHEN SIZE(null_pvs) > 0
          THEN null_pvs
        ELSE [null]
      END AS pvs
    WHERE size(pvs) > 0
    UNWIND pvs AS pv
    // for each pv, obtain the NCIt term associated with it, according to caDSR, and
    // synonyms (if any)
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {{origin_name: "NCIt"}}), (c_cadsr)-[:has_tag]->(:tag {{key: "mapping_source", value: "caDSR"}})
    // find any synonyms associated with the NCIt term in the NCI Metathesaurus data
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term), (c_ncim)-[:has_tag]->(:tag {{key: "mapping_source", value: "NCIm"}})
      WHERE pv IS NOT NULL AND pv <> syn AND pv.value <> syn.value
    WITH cde, pv, models, pv.value as pv_val, ncit_term.origin_id AS ncit_oid,
      ncit_term.value AS ncit_value,
      collect(DISTINCT syn.value) AS distinct_syn_vals WITH cde, models, pv_val,
      ncit_oid,
      CASE WHEN ncit_value IS NOT NULL THEN distinct_syn_vals + [ncit_value] ELSE distinct_syn_vals END AS syn_vals
    WITH cde, models,
      CASE WHEN pv_val IS NOT NULL THEN collect({{value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}}) ELSE [] END AS formatted_pvs
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
