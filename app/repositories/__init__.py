"""
Repositórios para acesso a dados.

Implementam o padrão Repository para abstração do acesso ao banco de dados.
"""

from app.repositories.base import BaseRepository
from app.repositories.ship_repository import ShipRepository
from app.repositories.ais_repository import AISRepository
from app.repositories.event_repository import EventRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.inspection_repository import InspectionRepository
from app.repositories.biofouling_repository import BiofoulingRepository

__all__ = [
    "BaseRepository",
    "ShipRepository",
    "AISRepository",
    "EventRepository",
    "AlertRepository",
    "InspectionRepository",
    "BiofoulingRepository",
]
