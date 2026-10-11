from fastapi.testclient import TestClient


def test_create_incident_citizen(client: TestClient, citizen_token_headers, sample_zone):
    payload = {
        "category": "landslide",
        "description": "Loose soil and small boulders blocking northbound single lane.",
        "latitude": 30.381,
        "longitude": 78.076,
        "landmark": "Near milestone 12",
        "severity": "medium",
    }
    response = client.post("/api/v1/incidents", json=payload, headers=citizen_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "landslide"
    assert data["status"] == "submitted"
    assert data["zone_id"] == str(sample_zone.id)  # Auto-detected from GPS


def test_admin_update_incident_status(
    client: TestClient,
    citizen_token_headers,
    admin_token_headers,
    sample_zone,
):
    # 1. Create incident as citizen
    create_resp = client.post(
        "/api/v1/incidents",
        json={
            "category": "flood",
            "description": "Drain overflowing across highway pavement.",
            "latitude": 30.380,
            "longitude": 78.075,
            "severity": "high",
        },
        headers=citizen_token_headers,
    )
    inc_id = create_resp.json()["id"]

    # 2. Admin verifies
    patch_resp = client.patch(
        f"/api/v1/incidents/{inc_id}/status",
        json={"status": "verified", "admin_note": "Inspection confirmed by SDRF."},
        headers=admin_token_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "verified"
    assert patch_resp.json()["admin_note"] == "Inspection confirmed by SDRF."


def test_citizen_cannot_change_incident_status(
    client: TestClient,
    citizen_token_headers,
    sample_zone,
):
    create_resp = client.post(
        "/api/v1/incidents",
        json={
            "category": "road_block",
            "description": "Fallen tree branch.",
            "latitude": 30.380,
            "longitude": 78.075,
        },
        headers=citizen_token_headers,
    )
    inc_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/incidents/{inc_id}/status",
        json={"status": "verified"},
        headers=citizen_token_headers,
    )
    assert patch_resp.status_code == 403


def test_get_nearby_incidents(client: TestClient, citizen_token_headers):
    client.post(
        "/api/v1/incidents",
        json={
            "category": "unsafe_route",
            "description": "Deep ditch on roadside edge.",
            "latitude": 30.3800,
            "longitude": 78.0750,
        },
        headers=citizen_token_headers,
    )

    response = client.get("/api/v1/incidents/nearby?latitude=30.3805&longitude=78.0755&radius_km=5.0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "distance_km" in data[0]
