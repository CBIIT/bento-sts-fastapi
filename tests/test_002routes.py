# tests/test_routes.py
import pytest

class TestTagsRouter:
    """Tests for /tags endpoints"""
    
    def test_tags_get(self, test_sts_client):
        response = test_sts_client.get("/v2/tags")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_tags_get_with_pagination(self, test_sts_client):
        response = test_sts_client.get("/v2/tags?skip=0&limit=5")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) <= 5
    
    def test_tags_count_get(self, test_sts_client):
        response = test_sts_client.get("/v2/tags/count")
        assert response.status_code == 200
        assert isinstance(response.json(), int)


class TestTagRouter:
    """Tests for /tag endpoints"""
    
    def test_tag_key_values_get(self, test_sts_client):
        # First get a tag to use its key
        tags_response = test_sts_client.get("/v2/tags?limit=1")
        if tags_response.json():
            tag_key = tags_response.json()[0]["key"]
            response = test_sts_client.get(f"/v2/tag/{tag_key}/values")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    def test_tag_key_values_get_invalid(self, test_sts_client):
        response = test_sts_client.get("/v2/tag/nonexistent_key/values")
        assert response.status_code == 404
        assert response.json()['detail'] == "Not found."
    
    def test_tag_key_value_entities_get(self, test_sts_client):
        # Get a tag first
        tags_response = test_sts_client.get("/v2/tags?limit=1")
        if tags_response.json():
            tag = tags_response.json()[0]
            response = test_sts_client.get(
                f"/v2/tag/{tag['key']}/{tag['value']}/entities"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    def test_tag_key_value_entities_count_get(self, test_sts_client):
        tags_response = test_sts_client.get("/v2/tags?limit=1")
        if tags_response.json():
            tag = tags_response.json()[0]
            response = test_sts_client.get(
                f"/v2/tag/{tag['key']}/{tag['value']}/entities/count"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), int)

    # Cypher that finds (key, value) pairs where any entity is connected via
    # more than one has_tag edge — these are exactly the cases that produce
    # duplicates.
    _MULTI_EDGE_TAGS_STMT = (
        "MATCH (n1)-[r:has_tag]->(t:tag) "
        "WITH n1.nanoid AS nanoid, t.key AS key, t.value AS value, count(r) AS cnt "
        "WHERE cnt > 1 "
        "RETURN DISTINCT key, value "
        "LIMIT 50"
    )

    def test_entities_no_duplicates_for_multi_edge_tags(
        self, test_sts_client, test_sts_mdb
    ):
        """Entities connected via multiple has_tag edges must appear only once."""
        rows = test_sts_mdb.get_with_statement(
            self._MULTI_EDGE_TAGS_STMT, {}, raise_on_empty=False
        )
        duplicates_found = []
        for row in rows:
            key, value = row["key"], row["value"]
            response = test_sts_client.get(f"/v2/tag/{key}/{value}/entities")
            assert response.status_code == 200, (
                f"Unexpected status for tag key='{key}' value='{value}'"
            )
            nanoids = [e["nanoid"] for e in response.json() if e.get("nanoid")]
            dupes = [nid for nid in set(nanoids) if nanoids.count(nid) > 1]
            if dupes:
                duplicates_found.append(
                    f"key='{key}' value='{value}' → duplicated nanoids: {dupes}"
                )

        assert not duplicates_found, (
            "Duplicate nanoids in /entities response (DISTINCT missing?):\n"
            + "\n".join(duplicates_found)
        )

    def test_entities_count_matches_list_for_multi_edge_tags(
        self, test_sts_client, test_sts_mdb
    ):
        """/entities/count must equal len(/entities) for tags with multi-edge entities."""
        rows = test_sts_mdb.get_with_statement(
            self._MULTI_EDGE_TAGS_STMT, {}, raise_on_empty=False
        )
        mismatches = []
        for row in rows:
            key, value = row["key"], row["value"]
            list_resp = test_sts_client.get(f"/v2/tag/{key}/{value}/entities")
            count_resp = test_sts_client.get(f"/v2/tag/{key}/{value}/entities/count")
            assert list_resp.status_code == 200
            assert count_resp.status_code == 200
            actual = len(list_resp.json())
            reported = count_resp.json()
            if actual != reported:
                mismatches.append(
                    f"key='{key}' value='{value}' → list={actual}, count={reported}"
                )

        assert not mismatches, (
            "Count mismatch between /entities and /entities/count:\n"
            + "\n".join(mismatches)
        )


class TestModelsRouter:
    """Tests for /models endpoints"""
    
    def test_models_get(self, test_sts_client):
        response = test_sts_client.get("/v2/models")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_models_get_with_pagination(self, test_sts_client):
        response = test_sts_client.get("/v2/models?skip=0&limit=2")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) <= 2
    
    def test_models_count_get(self, test_sts_client):
        response = test_sts_client.get("/v2/models/count")
        assert response.status_code == 200
        assert isinstance(response.json(), int)
        assert response.json() >= 0


class TestModelRouter:
    """Tests for /model endpoints"""
    
    @pytest.fixture
    def model_info(self, test_sts_client):
        """Get a model to use in tests"""
        response = test_sts_client.get("/v2/models?limit=1")
        if response.json():
            return response.json()[0]
        return None
    
    def test_model_versions_get(self, test_sts_client, model_info):
        if model_info:
            response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/versions"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    def test_model_versions_get_invalid(self, test_sts_client):
        response = test_sts_client.get("/v2/model/nonexistent_model/versions")
        assert response.status_code == 404
        assert response.json()['detail'] == "Not found."
    
    def test_model_latest_version_get(self, test_sts_client, model_info):
        if model_info:
            response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/latest-version"
            )
            assert response.status_code == 200
            assert "name" in response.json()
            assert "version" in response.json()
    
    def test_model_nodes_get(self, test_sts_client, model_info):
        if model_info:
            response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/version/{model_info['version']}/nodes"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    def test_model_nodes_count_get(self, test_sts_client, model_info):
        if model_info:
            response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/version/{model_info['version']}/nodes/count"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), int)
    
    def test_model_node_get(self, test_sts_client, model_info):
        if model_info:
            # Get a node first
            nodes_response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/version/{model_info['version']}/nodes?limit=1"
            )
            if nodes_response.json():
                node = nodes_response.json()[0]
                response = test_sts_client.get(
                    f"/v2/model/{model_info['name']}/version/{model_info['version']}/node/{node['handle']}"
                )
                assert response.status_code == 200
                assert response.json()["handle"] == node["handle"]
    
    def test_model_node_properties_get(self, test_sts_client, model_info):
        if model_info:
            nodes_response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/version/{model_info['version']}/nodes?limit=1"
            )
            if nodes_response.json():
                node = nodes_response.json()[0]
                response = test_sts_client.get(
                    f"/v2/model/{model_info['name']}/version/{model_info['version']}/node/{node['handle']}/properties"
                )
                assert response.status_code == 200
                assert isinstance(response.json(), list)
    
    def test_model_node_properties_count_get(self, test_sts_client, model_info):
        if model_info:
            nodes_response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/version/{model_info['version']}/nodes?limit=1"
            )
            if nodes_response.json():
                node = nodes_response.json()[0]
                response = test_sts_client.get(
                    f"/v2/model/{model_info['name']}/version/{model_info['version']}/node/{node['handle']}/properties/count"
                )
                assert response.status_code == 200
                assert isinstance(response.json(), int)
    
    def test_model_node_property_get(self, test_sts_client, model_info):
        if model_info:
            nodes_response = test_sts_client.get(
                f"/v2/model/{model_info['name']}/version/{model_info['version']}/nodes?limit=1"
            )
            if nodes_response.json():
                node = nodes_response.json()[0]
                props_response = test_sts_client.get(
                    f"/v2/model/{model_info['name']}/version/{model_info['version']}/node/{node['handle']}/properties?limit=1"
                )
                if props_response.json():
                    prop = props_response.json()[0]
                    response = test_sts_client.get(
                        f"/v2/model/{model_info['name']}/version/{model_info['version']}/node/{node['handle']}/property/{prop['handle']}"
                    )
                    assert response.status_code == 200
                    assert response.json()["handle"] == prop["handle"]
    
    def test_model_node_property_terms_get(self, test_sts_client):
        # test a property that has terms and one that doesn't
        response = test_sts_client.get("/v2/model/CTDC/version/1.7.0/node/principal_investigator_not_exists"
                                       "/property/person_orcid/terms")
        assert response.status_code == 404
        assert response.json()['detail'] == "Not found."

        response = test_sts_client.get("/v2/model/CTDC/version/1.7.0/node/principal_investigator"
                                       "/property/person_orcid/terms")
        assert response.status_code == 404
        assert response.json()['detail'] == "Property exists, but does not use an acceptable value set."

        response = test_sts_client.get("/v2/model/CTDC/version/1.7.0/node/diagnosis"
                                       "/property/meddra_disease_code/terms")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    def test_model_node_property_terms_count_get(self, test_sts_client, model_info):
        response = test_sts_client.get("/v2/model/CTDC/version/1.7.0/node/diagnosis"
                                       "/property/meddra_disease_code/terms/count")
        assert response.status_code == 200
        assert isinstance(response.json(), int)
    
    def test_model_node_property_term_get(self, test_sts_client):
        # Use a known valid term value from the test data
        term_value = "10010029"
        response = test_sts_client.get(
            f"/v2/model/CTDC/version/1.7.0/node/diagnosis"
            f"/property/meddra_disease_code/term/{term_value}"
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["value"] == term_value
        assert "type" in response.json()[0]
        assert response.json()[0]["type"] == "Term"

    def test_model_node_property_term_get_invalid(self, test_sts_client):
        # Test with non-existent term value
        response = test_sts_client.get("/v2/model/CTDC/version/1.7.0/node/diagnosis"
                                      "/property/meddra_disease_code/term/nonexistent_term_value")
        assert response.status_code == 404
        assert response.json()['detail'] == "Not found."

    def test_model_node_property_term_get_with_space_and_comma(self, test_sts_client):
        """
        Test term endpoint with both spaces and comma in term value.
        """
        # Test with a term that contains both spaces and comma
        term_value = "C05.1 : Soft palate, NOS"
        
        response = test_sts_client.get(
            f"/v2/model/C3DC/version/4.0.5/node/diagnosis"
            f"/property/anatomic_site/term/{term_value}"
        )
        
        assert response.status_code == 200
        assert response.json() is not None
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["value"] == term_value
        assert response.json()[0]["type"] == "Term"


class TestIdRouter:
    """Tests for /id endpoints"""
    
    def test_id_get_valid(self, test_sts_client):
        response = test_sts_client.get("/v2/id/i17AaX")
        assert response.status_code == 200
    
    def test_id_get_invalid(self, test_sts_client):
        response = test_sts_client.get("/v2/id/i17Aa")
        assert response.status_code == 404
        assert response.json()['detail'] == 'Not found.';


class TestTermsRouter:
    """Tests for /terms endpoints"""
    
    @pytest.fixture
    def model_info(self, test_sts_client):
        """Get a model to use in tests"""
        response = test_sts_client.get("/v2/models?limit=1")
        if response.json():
            return response.json()[0]
        return None
    
    def test_pvs_synonyms_model_version_get(self, test_sts_client, model_info):
        if model_info:
            response = test_sts_client.get(
                f"/v2/terms/model-pvs/{model_info['name']}/?version={model_info['version']}"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    def test_pvs_synonyms_model_version_get_with_property(self, test_sts_client, model_info):
        if model_info:
            # Get the first property from the model
            props_response = test_sts_client.get(
                f"/v2/terms/model-pvs/{model_info['name']}/?version={model_info['version']}&limit=1"
            )

            assert props_response.status_code == 200
            assert isinstance(props_response.json(), list)

            if props_response.json():
                prop_handle = props_response.json()[0]["property"]
                response = test_sts_client.get(
                    f"/v2/terms/model-pvs/{model_info['name']}/{prop_handle}?version={model_info['version']}"
                )
                assert response.status_code == 200
                assert isinstance(response.json(), list)
    
    def test_pvs_synonyms_model_version_get_with_pagination(self, test_sts_client, model_info):
        if model_info:
            response = test_sts_client.get(
                f"/v2/terms/model-pvs/{model_info['name']}/?version={model_info['version']}&skip=0&limit=5"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), list)
            # Check that each property's permissibleValues array is limited to 5 or less
            for item in response.json():
                assert 'permissibleValues' in item
                assert len(item['permissibleValues']) <= 5

    def test_pvs_synonyms_model_version_get_invalid_model(self, test_sts_client):
        response = test_sts_client.get(
            "/v2/terms/model-pvs/nonexistent_model/?version=1.0.0"
        )
        assert response.status_code == 404
        assert response.json()['detail'] == "Not found."
    
    def test_cde_pvs_by_id_with_version_get(self, test_sts_client):
        # Test with a specific CDE ID if you know one exists
        response = test_sts_client.get("/v2/terms/cde-pvs/4723846/1/pvs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_cde_pvs_by_id_without_version_get(self, test_sts_client):
        response = test_sts_client.get("/v2/terms/cde-pvs/test_id/none/pvs")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_cde_pvs_by_id_with_empty_pvs(self, test_sts_client):
        # Test CDE that exists but has no permissible values
        response = test_sts_client.get("/v2/terms/cde-pvs/2413278/1.20/pvs")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['CDECode'] == '2413278'
        assert result[0]['CDEVersion'] == '1.20'
        assert result[0]['permissibleValues'] == []


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_invalid_pagination_params(self, test_sts_client):
        response = test_sts_client.get("/v2/tags?skip=-1&limit=-5")
        assert response.status_code == 422
    
    def test_very_large_limit(self, test_sts_client):
        response = test_sts_client.get("/v2/tags?limit=1000000")
        assert response.status_code == 200
    
    def test_special_characters_in_params(self, test_sts_client):
        response = test_sts_client.get("/v2/tag/key%20with%20spaces/value")
        # Should handle URL encoding
        assert response.status_code in [200, 404]
    
    def test_empty_path_params(self, test_sts_client):
        response = test_sts_client.get("/v2/model//versions")
        assert response.status_code == 404

