# AGENT.md — HimalayaSense Build Instructions

## Project Overview

**HimalayaSense** is an early-warning and citizen-reporting decision-support system for landslides, flash-floods, and unsafe road corridors in Uttarakhand, India (pilot region: Dehradun district).

## Target Architecture

- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Database**: PostgreSQL (Production) / SQLite (Development Fallback)
- **ML Engine**: Scikit-Learn (RandomForest) & XGBoost, feature engineering pipeline
- **Weather Ingestion**: Open-Meteo Forecast & Historical API
- **Background Jobs**: APScheduler
- **Notifications**: In-app emergency alerts & SMTP email dispatch
- **Storage**: Local `/uploads` for citizen photos

## Repository Tree

```text
himalayasense/
├── AGENT.md
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── api.py
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── zones.py
│   │   │       ├── incidents.py
│   │   │       ├── weather.py
│   │   │       ├── risk.py
│   │   │       ├── alerts.py
│   │   │       └── admin.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── crud/
│   │   ├── services/
│   │   ├── ml/
│   │   ├── workers/
│   │   └── tests/
│   ├── requirements.txt
│   ├── alembic/
│   ├── alembic.ini
│   ├── seed.py
│   └── .env.example
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
└── docs/
    ├── architecture.md
    ├── api.md
    ├── database.md
    └── ml.md
```
