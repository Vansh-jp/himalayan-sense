from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.zones import router as zones_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.weather import router as weather_router
from app.api.v1.risk import router as risk_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(zones_router)
api_router.include_router(incidents_router)
api_router.include_router(weather_router)
api_router.include_router(risk_router)
api_router.include_router(alerts_router)
api_router.include_router(admin_router)
