# HimalayaSense API Documentation

Base URI: `/api/v1`
Interactive Swagger Docs: `http://localhost:8000/docs`

## 1. Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register citizen user with name, email, password, phone, district | None |
| `POST` | `/api/v1/auth/login` | Login with email and password returning JWT access & refresh tokens | None |
| `POST` | `/api/v1/auth/refresh` | Obtain new access token with valid refresh token | None |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile | Bearer Token |

## 2. Zones & Risk

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/zones` | List all monitored zones | None |
| `GET` | `/api/v1/zones/{zone_id}` | Retrieve specific zone metadata and polygon | None |
| `GET` | `/api/v1/zones/{zone_id}/current-risk` | Real-time risk status, color, weather, active incidents | None |
| `GET` | `/api/v1/risk/map` | GeoJSON map feed with color-coded risk and stats | None |
| `GET` | `/api/v1/risk/history` | Historical risk assessments query | None |
| `POST` | `/api/v1/risk/recalculate` | Trigger system-wide risk recalculation | None |

## 3. Incident Management

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/incidents` | Citizen submits incident report with GPS & photo | Bearer Token |
| `POST` | `/api/v1/incidents/upload` | Upload incident photo to local `/uploads` storage | Bearer Token |
| `GET` | `/api/v1/incidents` | List reports with category, status, severity, zone filters | None |
| `GET` | `/api/v1/incidents/{incident_id}` | Get incident report details | None |
| `PATCH` | `/api/v1/incidents/{incident_id}/status` | Admin status update: verified, in_progress, resolved, rejected | Admin Token |
| `GET` | `/api/v1/incidents/nearby` | Haversine radius search for nearby incidents | None |

## 4. Weather Ingestion

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/weather/current` | Current temperature, precipitation, 24h totals | None |
| `GET` | `/api/v1/weather/forecast` | 24h, 48h, 72h forecast precipitation and hourly series | None |
| `POST` | `/api/v1/weather/ingest` | Manual trigger for Open-Meteo ingestion | Admin Token |

## 5. Alerts

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/alerts` | List active emergency alerts | None |
| `GET` | `/api/v1/alerts/{alert_id}` | Alert details and delivery status | None |
| `POST` | `/api/v1/alerts/subscribe` | Citizen subscription to email/SMS broadcasts | None / Optional |
| `GET` | `/api/v1/alerts/my` | User-targeted notifications | Bearer Token |

## 6. Admin Analytics

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/admin/analytics/overview` | Overall KPI summary (incidents, resolution time, high risk zones) | Admin Token |
| `GET` | `/api/v1/admin/analytics/incidents` | Incidents by category, by zone, by status, and 7d trend | Admin Token |
| `GET` | `/api/v1/admin/analytics/risk` | Zone-wise risk comparison and rainfall scatter data | Admin Token |
| `GET` | `/api/v1/admin/analytics/alerts` | Alert delivery stats and channel breakdown | Admin Token |
