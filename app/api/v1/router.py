"""
Router principal da API v1.

Agrega todos os routers de endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import ships, biofouling, alerts, predictions, roi, ais, analytics, reports

# Router principal
api_router = APIRouter()

# Incluir sub-routers
api_router.include_router(
    ships.router,
    prefix="/ships",
    tags=["Ships"]
)

api_router.include_router(
    biofouling.router,
    prefix="/biofouling",
    tags=["Biofouling"]
)

api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts"]
)

api_router.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"]
)

api_router.include_router(
    roi.router,
    prefix="/roi",
    tags=["ROI"]
)

api_router.include_router(
    ais.router,
    prefix="/ais",
    tags=["AIS"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)
