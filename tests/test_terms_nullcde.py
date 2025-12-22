null_pvs = {'Not Assessed', 'Not Asked', 'Temporarily Unavailable', 'Insufficient Quantity', 'Technical Problem', 'Response Declined', 'Not Specified', 'Unknown', 'Not Evaluable', 'Not Reported', 'Not Otherwise Specified', 'Not Applicable', 'Not Allowed To Collect', 'Censored'}

def test_model_pvs_with_nullCDE(test_sts_client):
    # Test pvs_synonyms_model_version_get endpoint with library_layout property that has useNullCDE tag
    response = test_sts_client.get("/v2/terms/model-pvs/CDS/library_layout?skip=0&limit=0&use_null_cde=true")
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    
    # Check that the response is for the correct property and model
    assert content[0]['property'] == 'library_layout', f"Expected property 'library_layout', got {content[0]['property']}"
    assert content[0]['model'] == 'CDS', f"Expected model 'CDS', got {content[0]['model']}"
    
    # Get the PV values
    pvs_for_library_layout = [pv['value'] for pv in content[0]['permissibleValues']]
    count_with_null = len(pvs_for_library_layout)
    
    # Test without null CDE
    response_no_null = test_sts_client.get("/v2/terms/model-pvs/CDS/library_layout?skip=0&limit=0&use_null_cde=false")
    assert response_no_null.status_code == 200
    content_no_null = response_no_null.json()
    pvs_no_null = [pv['value'] for pv in content_no_null[0]['permissibleValues']]
    count_without_null = len(pvs_no_null)
    
    # With NULL CDE should have at least as many PVs as without
    assert count_with_null >= count_without_null, f"Expected at least as many PVs with null CDE ({count_with_null}) as without ({count_without_null})"
    
    # If NULL CDE data exists in test env (count is higher when use_null_cde=true)
    if count_with_null > count_without_null:
        # Check that null_pvs (NULL CDE values) are actually included
        null_pvs_found = null_pvs & set(pvs_for_library_layout)
        assert len(null_pvs_found) > 0, f"Expected NULL CDE values to be included when count increased. NULL PVs found: {null_pvs_found}, All PVs: {pvs_for_library_layout}"
        
        # Check that all null_pvs are in the pvs returned for library layout
        assert null_pvs < set(pvs_for_library_layout), f"Expected all NULL PVs to be included."
        
        # Check that the model-specified values are also returned
        assert set(["Paired-End", "Single-indexed"]) < set(pvs_for_library_layout), f"Expected model values in: {pvs_for_library_layout}"
        
        # Verify NULL PVs are NOT in the response when use_null_cde=false
        null_pvs_in_no_null = null_pvs & set(pvs_no_null)
        assert len(null_pvs_in_no_null) == 0, f"Expected NO NULL PVs when use_null_cde=false, but found: {null_pvs_in_no_null}"

def test_cde_pvs_with_nullCDE(test_sts_client):
    # Test cde_pvs_by_id_with_version_get endpoint with a CDE that has useNullCDE tag
    response = test_sts_client.get("/v2/terms/cde-pvs/15235975/1.00/pvs?use_null_cde=true")
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    # Get the PV values
    pvs = [pv['value'] for pv in content[0]['permissibleValues']]
    count_with_null = len(pvs)
    
    # Test without null CDE
    response_no_null = test_sts_client.get("/v2/terms/cde-pvs/15235975/1.00/pvs?use_null_cde=false")
    assert response_no_null.status_code == 200
    content_no_null = response_no_null.json()
    pvs_no_null = [pv['value'] for pv in content_no_null[0]['permissibleValues']]
    count_without_null = len(pvs_no_null)
    
    # With NULL CDE should have at least as many PVs as without
    assert count_with_null >= count_without_null, f"Expected at least as many PVs with null CDE ({count_with_null}) as without ({count_without_null})"
    
    # If NULL CDE data exists in test env (count is higher when use_null_cde=true)
    if count_with_null > count_without_null:
        # The difference should be in null_pvs
        added_pvs = set(pvs) - set(pvs_no_null)
        assert len(added_pvs & null_pvs) > 0, f"Expected added PVs to be NULL CDE values. Added: {added_pvs}, NULL PVs: {null_pvs}"
