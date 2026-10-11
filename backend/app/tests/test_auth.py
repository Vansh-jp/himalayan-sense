from fastapi.testclient import TestClient


def test_register_citizen_success(client: TestClient):
    payload = {
        "name": "Sunil Negi",
        "email": "sunil.negi@himalayasense.local",
        "password": "Password123!",
        "phone": "+91-9876543299",
        "district": "Dehradun",
        "role": "citizen",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "sunil.negi@himalayasense.local"
    assert data["user"]["role"] == "citizen"


def test_register_duplicate_email_fails(client: TestClient, citizen_user):
    payload = {
        "name": "Duplicate User",
        "email": citizen_user.email,
        "password": "Password123!",
        "district": "Dehradun",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client: TestClient, citizen_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": citizen_user.email, "password": "Citizen@12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == str(citizen_user.id)


def test_login_invalid_password(client: TestClient, citizen_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": citizen_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401


def test_refresh_token(client: TestClient, citizen_user):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": citizen_user.email, "password": "Citizen@12345"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


def test_get_current_user_me(client: TestClient, citizen_token_headers, citizen_user):
    response = client.get("/api/v1/auth/me", headers=citizen_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(citizen_user.id)
    assert data["email"] == citizen_user.email


def test_protected_route_without_token_fails(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
