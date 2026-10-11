from fastapi.testclient import TestClient


def test_list_zones(client: TestClient, sample_zone):
    response = client.get("/api/v1/zones")
    assert response.status_code == 200
    zones = response.json()
    assert len(zones) >= 1
    assert any(z["name"] == sample_zone.name for z in zones)


def test_get_zone_by_id(client: TestClient, sample_zone):
    response = client.get(f"/api/v1/zones/{sample_zone.id}")
    assert response.status_code == 200
    assert response.json()["name"] == sample_zone.name


def test_get_zone_current_risk(client: TestClient, sample_zone):
    response = client.get(f"/api/v1/zones/{sample_zone.id}/current-risk")
    assert response.status_code == 200
    data = response.json()
    assert "current_risk_level" in data
    assert "risk_score" in data
    assert "risk_color" in data


def test_admin_create_zone(client: TestClient, admin_token_headers):
    payload = {
        "name": "New Test Ward",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.33,
        "longitude": 78.05,
        "terrain_susceptibility_score": 0.4,
        "historical_incident_count": 2,
        "boundary_geojson": {"type": "Polygon", "coordinates": []},
    }
    response = client.post("/api/v1/zones", json=payload, headers=admin_token_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "New Test Ward"


def test_citizen_cannot_create_zone(client: TestClient, citizen_token_headers):
    payload = {
        "name": "Unauthorized Ward",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.33,
        "longitude": 78.05,
        "boundary_geojson": {},
    }
    response = client.post("/api/v1/zones", json=payload, headers=citizen_token_headers)
    assert response.status_code == 403
