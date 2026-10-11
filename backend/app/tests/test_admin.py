from fastapi.testclient import TestClient


def test_admin_analytics_overview(client: TestClient, admin_token_headers):
    response = client.get("/api/v1/admin/analytics/overview", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_incidents" in data
    assert "pending_verification" in data
    assert "total_zones" in data


def test_admin_analytics_incidents(client: TestClient, admin_token_headers):
    response = client.get("/api/v1/admin/analytics/incidents", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "by_category" in data
    assert "by_zone" in data
    assert "timeline_7d" in data


def test_admin_analytics_risk(client: TestClient, admin_token_headers):
    response = client.get("/api/v1/admin/analytics/risk", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data
    assert "rainfall_vs_incidents" in data


def test_admin_analytics_alerts(client: TestClient, admin_token_headers):
    response = client.get("/api/v1/admin/analytics/alerts", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data
    assert "by_level" in data


def test_citizen_cannot_access_analytics(client: TestClient, citizen_token_headers):
    response = client.get("/api/v1/admin/analytics/overview", headers=citizen_token_headers)
    assert response.status_code == 403
