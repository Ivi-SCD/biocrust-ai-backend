"""
Modelos SQLAlchemy para o sistema de bioincrustação.

Define todas as entidades do banco de dados.
"""

from app.models.ship import Ship, ShipEnvironmentalMetrics
from app.models.ais_position import AISPosition
from app.models.navigation_event import NavigationEvent
from app.models.fuel_consumption import FuelConsumption
from app.models.inspection import Inspection
from app.models.biofouling_index import BiofoulingIndex
from app.models.alert import Alert
from app.models.user import User
from app.models.report import Report

__all__ = [
    "Ship",
    "ShipEnvironmentalMetrics",
    "AISPosition",
    "NavigationEvent",
    "FuelConsumption",
    "Inspection",
    "BiofoulingIndex",
    "Alert",
    "User",
    "Report",
]
