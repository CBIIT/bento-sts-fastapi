null_pvs = {'Not Assessed', 'Not Asked', 'Temporarily Unavailable', 'Insufficient Quantity', 'Technical Problem', 'Response Declined', 'Not Specified', 'Unknown', 'Not Evaluable', 'Not Reported', 'Not Otherwise Specified', 'Not Applicable', 'Not Allowed To Collect', 'Censored'}

def test_model_pvs_with_nullCDE(test_sts_client):
    # Test property with useNullCDE tag (library_layout should have the tag)
    response = test_sts_client.get("/v2/terms/model-pvs/CDS/library_layout?skip=0&limit=0")
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    
    # Check that the response is for the correct property and model
    assert content[0]['property'] == 'library_layout', f"Expected property 'library_layout', got {content[0]['property']}"
    assert content[0]['model'] == 'CDS', f"Expected model 'CDS', got {content[0]['model']}"
    
    # Get the PV values - should include null CDE PVs if the property has the useNullCDE tag
    pvs_for_library_layout = [pv['value'] for pv in content[0]['permissibleValues']]
    
    # If NULL CDE data exists in test env and the property has useNullCDE tag
    # Check that null_pvs (NULL CDE values) are actually included
    null_pvs_found = null_pvs & set(pvs_for_library_layout)
    if len(null_pvs_found) > 0:
        # Check that all null_pvs are in the pvs returned for library layout
        assert null_pvs < set(pvs_for_library_layout), f"Expected all NULL PVs to be included."
        
        # Check that the model-specified values are also returned
        assert set(["Paired-End", "Single-indexed"]) < set(pvs_for_library_layout), f"Expected model values in: {pvs_for_library_layout}"

def test_cde_pvs_with_nullCDE(test_sts_client):
    # Test with use_null_cde=true (should include null CDE PVs regardless of property tags)
    response = test_sts_client.get("/v2/terms/cde-pvs/15235975/1.00/pvs?use_null_cde=true")
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    # Get the PV values
    pvs_with_flag = [pv['value'] for pv in content[0]['permissibleValues']]
    
    # Test without flag (use_null_cde=false, should NOT include null CDE PVs)
    response_no_flag = test_sts_client.get("/v2/terms/cde-pvs/15235975/1.00/pvs?use_null_cde=false")
    assert response_no_flag.status_code == 200
    content_no_flag = response_no_flag.json()
    pvs_no_flag = [pv['value'] for pv in content_no_flag[0]['permissibleValues']]
    
    # Test default behavior (no parameter, defaults to use_null_cde=false)
    response_default = test_sts_client.get("/v2/terms/cde-pvs/15235975/1.00/pvs")
    assert response_default.status_code == 200
    content_default = response_default.json()
    pvs_default = [pv['value'] for pv in content_default[0]['permissibleValues']]
    assert set(pvs_default) == set(pvs_no_flag), "Default behavior should be the same as use_null_cde=false"
    
    # With flag should have at least as many PVs as without flag
    assert len(pvs_with_flag) >= len(pvs_no_flag), f"Expected at least as many PVs with flag ({len(pvs_with_flag)}) as without ({len(pvs_no_flag)})"
    
    # If NULL CDE data exists in test env (count is higher when use_null_cde=true)
    if len(pvs_with_flag) > len(pvs_no_flag):
        # The difference should be null_pvs
        added_pvs = set(pvs_with_flag) - set(pvs_no_flag)
        assert len(added_pvs & null_pvs) > 0, f"Expected added PVs to be NULL CDE values. Added: {added_pvs}, NULL PVs: {null_pvs}"
        
        # Verify that null PVs are NOT in the default response (standardized behavior)
        null_pvs_in_default = null_pvs & set(pvs_default)
        assert len(null_pvs_in_default) == 0, f"Default response should NOT include null CDE PVs. Found: {null_pvs_in_default}"
