import pytest


def test_id_endpt(test_sts_client):
    response = test_sts_client.get("/v2/id/i17AaX")
    assert response.status_code == 200
    response = test_sts_client.get("/v2/id/i17Aa")
    print(response.json())
    assert response.status_code == 404
