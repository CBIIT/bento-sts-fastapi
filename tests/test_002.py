"""
Test for should_use_null_cde flag using test_data_setup fixture from conftest.py
"""

def test_should_use_null_cde_true_multiple_tags(test_data_setup):
    """Verify should_use_null_cde = True when property has multiple tags (True and "Yes")"""
    test_sts_mdb = test_data_setup

    stmt = """
    MATCH (p:property {handle: "age", model: "TestModel", version: "1.0"})
    -[:has_tag]->(use_null_tag:tag {key: "useNullCDE"})
    WITH p, use_null_tag,
      ANY(ut IN COLLECT(use_null_tag)
          WHERE ut.value IN ["Yes", "True"] OR ut.value = true)
        AS should_use_null_cde
    RETURN p.handle, use_null_tag.value, should_use_null_cde
    """

    result = test_sts_mdb.get_with_statement(stmt, {})

    assert len(result) >= 1, f"Expected at least 1 result, got {len(result)}"

    # Check that at least one result shows should_use_null_cde = True
    all_true = all(row['should_use_null_cde'] == True for row in result)
    
    print(f"\n✅ Test 1: should_use_null_cde = True (multiple tags: True and 'Yes')")
    print(f"   Property: {result[0]['p.handle']}")
    print(f"   All tag values and results:")
    for row in result:
        print(f"      - Tag Value: {row['use_null_tag.value']} (type: {type(row['use_null_tag.value']).__name__}) → {row['should_use_null_cde']}")

    assert all_true, "All tags should result in should_use_null_cde = True"


def test_should_use_null_cde_true_string_yes(test_data_setup):
    """Verify should_use_null_cde = True with single tag value "Yes" """
    test_sts_mdb = test_data_setup

    stmt = """
    MATCH (p:property {handle: "gender", model: "TestModel", version: "1.0"})
    -[:has_tag]->(use_null_tag:tag {key: "useNullCDE"})
    WITH p, use_null_tag,
      ANY(ut IN COLLECT(use_null_tag)
          WHERE ut.value IN ["Yes", "True"] OR ut.value = true)
        AS should_use_null_cde
    RETURN p.handle, use_null_tag.value, should_use_null_cde
    """

    result = test_sts_mdb.get_with_statement(stmt, {})

    assert len(result) == 1, f"Expected 1 result, got {len(result)}"

    row = result[0]
    print(f"\n✅ Test 2: should_use_null_cde = True (single tag: 'Yes')")
    print(f"   Property: {row['p.handle']}")
    print(f"   Tag Value: {row['use_null_tag.value']} (type: {type(row['use_null_tag.value']).__name__})")
    print(f"   Result: {row['should_use_null_cde']}")

    assert row['should_use_null_cde'] == True


def test_should_use_null_cde_false_string_no(test_data_setup):
    """Verify should_use_null_cde = False with single tag value "No" """
    test_sts_mdb = test_data_setup

    stmt = """
    MATCH (p:property {handle: "race", model: "TestModel", version: "1.0"})
    OPTIONAL MATCH (p)-[:has_tag]->(use_null_tag:tag {key: "useNullCDE"})
    WITH p, use_null_tag,
      ANY(ut IN COLLECT(use_null_tag)
          WHERE ut.value IN ["Yes", "True"] OR ut.value = true)
        AS should_use_null_cde
    RETURN p.handle, use_null_tag.value, should_use_null_cde
    """

    result = test_sts_mdb.get_with_statement(stmt, {})

    assert len(result) == 1, f"Expected 1 result, got {len(result)}"

    row = result[0]
    print(f"\n✅ Test 3: should_use_null_cde = False (single tag: 'No')")
    print(f"   Property: {row['p.handle']}")
    print(f"   Tag Value: {row['use_null_tag.value']} (type: {type(row['use_null_tag.value']).__name__})")
    print(f"   Result: {row['should_use_null_cde']}")

    assert row['should_use_null_cde'] == False
