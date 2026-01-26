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
    
    # Clean property: remove quotes and whitespace; Swagger doc requires to request a value input.
    property = property.strip().strip('"').strip("'").strip()
    
    # Build parameters and query based on whether property is specified
    has_property = property and property != ""
    params = {"p0": model, "p1": version, "p3": request.state.skip, "p4": request.state.limit} | ({"p2": property} if has_property else {})
    NULL_CDE_ID = '16476366|1'
    USE_NULL_CDE_TAG = 'useNullCDE'

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    stmt = f"""
    // Start with the model node and get the property (or all properties if not specified)
    MATCH (n0:node {{model:$p0}})-[r0:has_property]->(n1:property)
    WITH n1 AS prop
    WHERE n0.version = $p1""" + (" AND prop.handle = $p2" if has_property else "") + f"""
    // Get the CDE term associated with the property (if any)
    OPTIONAL MATCH (prop)-[:has_concept]->(c:concept)<-[:represents]-(cde:term)
      WHERE toLower(cde.origin_name) CONTAINS "cadsr"
    // Check if the property has the useNullCDE tag
    OPTIONAL MATCH (prop)-[:has_tag]->(use_null_tag:tag {{key: "{USE_NULL_CDE_TAG}"}})
    // Create CDE metadata and flag indicating if null CDE should be included for this property
    WITH prop, cde, use_null_tag, cde.origin_id AS CDECode, cde.origin_version AS CDEVersion,
      cde.value AS CDEFullName,
      cde.origin_id + "|" + COALESCE(cde.origin_version, "") AS cde_hdl,
      CASE WHEN cde IS NOT NULL THEN true ELSE false END AS has_cde,
      ANY(ut IN COLLECT(use_null_tag) WHERE ut.value IN ["Yes", "True", "true"] OR ut.value = true) AS should_use_null_cde
    // Get PVs defined in the MDF model for this property
    OPTIONAL MATCH (prop)-[:has_value_set]->(:value_set)-[:has_term]->(model_pv:term)
    WITH distinct prop.handle AS prop, cde, CDECode, CDEVersion, CDEFullName, cde_hdl, has_cde, should_use_null_cde,
      collect(DISTINCT model_pv) AS model_pvs
    // Get the CDE's official PVs from the value set
    OPTIONAL MATCH (v:value_set {{handle: cde_hdl}})-[:has_term]->(cde_pv:term)
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, has_cde, should_use_null_cde,
      collect(cde_pv) AS cde_pvs
    // Use the property's tag to determine null_cde
    OPTIONAL MATCH (null_vs:value_set {{handle: "{NULL_CDE_ID}"}})-[:has_term]->(null_pv:term)
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, cde_pvs, has_cde, should_use_null_cde,
      CASE WHEN should_use_null_cde THEN COLLECT(DISTINCT null_pv) ELSE [] END AS null_pvs
    // Get all unique alternate values for all CDE PVs 
    UNWIND CASE WHEN size(cde_pvs) > 0 THEN cde_pvs ELSE [null] END AS temp_pv
    OPTIONAL MATCH (temp_pv)-[:represents]->(c_alt:concept)<-[:represents]-(alt_pv:term {{origin_name: "caDSR_alternates"}}), (c_alt)-[:has_tag]->(:tag {{key: "mapping_source", value: "alternate_name"}})
      WHERE temp_pv <> alt_pv AND alt_pv.value IS NOT NULL
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, cde_pvs, null_pvs, has_cde, should_use_null_cde,
      collect(DISTINCT alt_pv.value) AS alternate_values
    // Determine which PV set to use based on availability and content
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, cde_pvs, null_pvs, alternate_values, has_cde,
      CASE WHEN has_cde and size(cde_pvs) > 0 AND ANY(p in cde_pvs WHERE p.value =~ "https?://.*")
          THEN true
        WHEN has_cde and size(cde_pvs) > 0 AND NONE(p in cde_pvs WHERE p.value =~ "https?://.*")
          THEN false
        ELSE true 
      END AS fall_back_to_model_pvs
    WITH prop, CDECode, CDEVersion, CDEFullName, model_pvs, fall_back_to_model_pvs, CASE WHEN fall_back_to_model_pvs THEN [] ELSE cde_pvs END AS pvs, null_pvs, CASE WHEN fall_back_to_model_pvs THEN [] ELSE alternate_values END AS alternate_values
    WITH prop, model_pvs, all(x IN collect(fall_back_to_model_pvs) WHERE x = true) AS overall_fall_back_flag, 
                          apoc.coll.toSet(apoc.coll.flatten(collect(DISTINCT pvs))) as pvs_list,
                          apoc.coll.toSet(apoc.coll.flatten(collect(DISTINCT null_pvs))) as null_pvs_list,
                          apoc.coll.toSet(apoc.coll.flatten(collect(DISTINCT alternate_values))) as alternate_values_list
    WITH prop, case when overall_fall_back_flag then model_pvs else pvs_list end as pvs, null_pvs_list, alternate_values_list
    WITH prop, alternate_values_list,
     apoc.coll.toSet(
       (CASE WHEN size(pvs) > 0 THEN pvs ELSE [] END) +
       (CASE WHEN size(null_pvs_list) > 0 THEN null_pvs_list ELSE [] END)
     ) AS pvs_all
    UNWIND CASE WHEN size(pvs_all) > 0 THEN pvs_all ELSE [null] END AS pv
    // For each PV, obtain the NCIt term associated with it according to caDSR
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {{origin_name: "NCIt"}}), (c_cadsr)-[:has_tag]->(:tag {{key: "mapping_source", value: "caDSR"}})
    // Find any synonyms associated with the NCIt term in the NCI Metathesaurus data
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term), (c_ncim)-[:has_tag]->(:tag {{key: "mapping_source", value: "NCIm"}})
      WHERE pv <> syn and pv.value <> syn.value
    WITH prop, alternate_values_list, pv.value AS pv_val,
      ncit_term.origin_id AS ncit_oid, ncit_term.value AS ncit_value,
      collect(DISTINCT syn.value) AS distinct_syn_vals
    WITH prop, alternate_values_list, pv_val, ncit_oid,
      CASE WHEN ncit_value IS NOT NULL
        THEN distinct_syn_vals + [ncit_value]
        ELSE distinct_syn_vals END AS syn_vals
    // Format the PVs with their synonyms and NCIt codes
    WITH prop, alternate_values_list,
      [pv_item IN apoc.coll.toSet(apoc.coll.flatten(collect(DISTINCT {{value: pv_val, synonyms: syn_vals, ncit_concept_code: ncit_oid}}))) WHERE pv_item.value IS NOT NULL] AS formatted_pvs
    // Extract regular PV values for deduplication
    WITH prop, formatted_pvs,
      [pv IN formatted_pvs | pv.value] AS regular_pv_values, alternate_values_list
    // Filter out null PVs and alternates in regular PVs
    WITH prop, formatted_pvs,
      [val IN alternate_values_list WHERE NOT val IN regular_pv_values | {{value: val, synonyms: []}}] AS formatted_alts
    // Combine formatted PVs with filtered null PVs and alternates PVs
    WITH prop, formatted_pvs + formatted_alts AS all_pvs
    // Return the results with pagination support

    RETURN DISTINCT $p0 AS model, $p1 AS version,
      prop AS property,
      CASE 
        WHEN $p4 > 0 THEN all_pvs[$p3..($p3 + $p4)]
        WHEN $p3 > 0 THEN all_pvs[$p3..]
        ELSE all_pvs
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
def cde_pvs_by_id_with_version_get(request: Request, id: str, version: str, use_null_cde: bool = False):
    NULL_CDE_ID = '16476366|1'

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    use_null = "true" if use_null_cde else "false"
    stmt = f"""
    // Start with the CDE term by origin_id and optionally version
    MATCH (n0:term {{origin_id: $p0 }})
      WHERE $p1 = "none" OR n0.origin_version = $p1
    // Get the CDE's official PVs from the value set
    OPTIONAL MATCH (vs:value_set)-[:has_term]->(pv:term)
      WHERE vs.handle = $p0 + '|' + coalesce(n0.origin_version, "")
    WITH n0, vs.url as value_set_url, COLLECT(pv) as pvs
    // Get the null CDE PVs only if use_null_cde flag is true
    OPTIONAL MATCH (null_vs:value_set {{handle: "{NULL_CDE_ID}"}})-[:has_term]->(null_pv:term)
    WITH n0, value_set_url, pvs,
      CASE WHEN {use_null} THEN COLLECT(DISTINCT null_pv) ELSE [] END AS null_pvs
    // Get all unique alternate values for CDE PVs only (not null PVs)
    UNWIND CASE WHEN size(pvs) > 0 THEN pvs ELSE [null] END AS temp_pv
    OPTIONAL MATCH (temp_pv)-[:represents]->(c_alt:concept)<-[:represents]-(alt_pv:term {{origin_name: "caDSR_alternates"}}), (c_alt)-[:has_tag]->(:tag {{key: "mapping_source", value: "alternate_name"}})
      WHERE temp_pv IS NOT NULL AND temp_pv <> alt_pv AND alt_pv.value IS NOT NULL
    WITH n0, value_set_url, pvs, null_pvs,
      collect(DISTINCT alt_pv.value) AS alternate_values
    // Get regular PV values for deduplication
    WITH n0, value_set_url, pvs, null_pvs, alternate_values,
      [pv IN pvs | pv.value] AS regular_pv_values
    // Combine regular PVs with null PVs (exclude duplicates)
    WITH n0, value_set_url, alternate_values,
      pvs + [npv IN null_pvs WHERE NOT npv.value IN regular_pv_values] AS all_pvs_combined
    // Process all PVs together (regular + null)
    UNWIND CASE WHEN size(all_pvs_combined) > 0 THEN all_pvs_combined ELSE [null] END AS pv
    // For each PV, obtain the NCIt term associated with it according to caDSR
    OPTIONAL MATCH (pv)-[:represents]->(c_cadsr:concept)<-[:represents]-(ncit_term:term {{origin_name: "NCIt"}}), (c_cadsr)-[:has_tag]->(:tag {{key: "mapping_source", value: "caDSR"}})
      WHERE pv IS NOT NULL
    // Find any synonyms associated with the NCIt term in the NCI Metathesaurus data
    OPTIONAL MATCH (ncit_term)-[:represents]->(c_ncim:concept)<-[:represents]-(syn:term), (c_ncim)-[:has_tag]->(:tag {{key: "mapping_source", value: "NCIm"}})
      WHERE pv IS NOT NULL AND pv <> syn and pv.value <> syn.value
    WITH n0, value_set_url, alternate_values,
      CASE WHEN pv IS NULL THEN null ELSE pv.value END as pv_val,
      CASE WHEN pv IS NULL THEN null ELSE ncit_term.origin_id END AS ncit_oid,
      CASE WHEN pv IS NULL THEN null ELSE ncit_term.value END AS ncit_value,
      collect(DISTINCT syn.value) AS distinct_syn_vals
    // Format the PVs with their synonyms and NCIt codes
    WITH n0, value_set_url, alternate_values,
      CASE WHEN pv_val IS NULL THEN [] ELSE collect({{value: pv_val, synonyms: CASE WHEN ncit_value IS NOT NULL THEN distinct_syn_vals + [ncit_value] ELSE distinct_syn_vals END, ncit_concept_code: ncit_oid}}) END AS permissibleValues
    // Extract all PV values for alternate deduplication
    WITH n0, permissibleValues,
      [pv IN permissibleValues | pv.value] AS all_pv_values,
      alternate_values
    // Filter out alternates already in PVs
    WITH n0, permissibleValues,
      [val IN alternate_values WHERE NOT val IN all_pv_values | {{value: val, ncit_concept_code: null, synonyms: []}}] AS formatted_alts
    // Combine formatted PVs with alternates
    WITH n0, permissibleValues + formatted_alts AS all_pvs
    // Return the CDE information with pagination support
    WITH n0.origin_id AS CDECode, n0.origin_version AS CDEVersion,
      n0.value AS CDEFullName, 
      CASE 
        WHEN $p3 > 0 THEN all_pvs[$p2..($p2 + $p3)]
        WHEN $p2 > 0 THEN all_pvs[$p2..]
        ELSE all_pvs
      END AS permissibleValues
    RETURN distinct CDECode, CDEVersion, CDEFullName, permissibleValues"""
    ret = request.state.mdb.get_with_statement(
        stmt,
        {"p0": id, "p1": version, "p2": request.state.skip, "p3": request.state.limit},
        raise_on_empty=False
    )
    return [record.data() if hasattr(record, 'data') else dict(record.items()) for record in ret]
