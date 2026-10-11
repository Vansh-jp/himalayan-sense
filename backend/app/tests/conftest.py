from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.zone import Zone

# In-memory SQLite database specifically for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db) -> User:
    user = User(
        name="Test Admin",
        email="testadmin@himalayasense.local",
        password_hash=hash_password("Admin@12345"),
        role="admin",
        district="Dehradun",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token_headers(admin_user: User) -> dict:
    token = create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def citizen_user(db) -> User:
    user = User(
        name="Test Citizen",
        email="testcitizen@himalayasense.local",
        password_hash=hash_password("Citizen@12345"),
        role="citizen",
        district="Dehradun",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def citizen_token_headers(citizen_user: User) -> dict:
    token = create_access_token(str(citizen_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_zone(db) -> Zone:
    zone = Zone(
        name="Test Rajpur Zone",
        district="Dehradun",
        state="Uttarakhand",
        zone_type="ward",
        latitude=30.3800,
        longitude=78.0750,
        terrain_susceptibility_score=0.75,
        historical_incident_count=5,
        boundary_geojson={
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.06, 30.36],
                    [78.09, 30.36],
                    [78.09, 30.40],
                    [78.06, 30.40],
                    [78.06, 30.36],
                ]],
            },
            "properties": {"name": "Test Rajpur Zone"},
        },
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone
