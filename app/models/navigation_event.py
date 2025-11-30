"""
Modelo de Evento de Navegação.

Representa eventos agregados diários de navegação.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.ship import Ship
    from app.models.fuel_consumption import FuelConsumption


class NavigationEvent(Base, UUIDMixin, TimestampMixin):
    """
    Evento de navegação agregado.
    
    Representa um período de navegação com métricas agregadas,
    geralmente correspondendo a um dia de operação.
    
    Attributes:
        id: UUID único do evento
        session_id: ID da sessão de navegação (do sistema legado)
        ship_id: UUID do navio
        event_name: Nome do evento (ex: "Navegação", "Fundeio")
        start_date: Data/hora de início
        end_date: Data/hora de fim
        duration_hours: Duração em horas
        distance_nm: Distância percorrida em milhas náuticas
        avg_speed: Velocidade média em nós
        aft_draft: Calado à ré em metros
        fwd_draft: Calado a vante em metros
        mid_draft: Calado a meia-nau em metros
        trim: Trim (diferença ré/vante) em metros
        displacement: Deslocamento em toneladas
        beaufort_scale: Escala Beaufort (0-12)
        sea_condition: Condição do mar
        latitude: Latitude média
        longitude: Longitude média
    """
    
    __tablename__ = "navigation_events"
    
    # ID da sessão (do sistema legado)
    session_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
        index=True
    )
    
    # Referência ao navio
    ship_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ships.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Identificação do evento
    event_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Período
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Métricas de navegação
    duration_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    distance_nm: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    avg_speed: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Calados
    aft_draft: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    fwd_draft: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    mid_draft: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    trim: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Características
    displacement: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    beaufort_scale: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    sea_condition: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Posição média
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Relacionamentos
    ship: Mapped["Ship"] = relationship(
        "Ship",
        back_populates="events"
    )
    
    fuel_consumption: Mapped[List["FuelConsumption"]] = relationship(
        "FuelConsumption",
        back_populates="navigation_event",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    # Índices
    __table_args__ = (
        Index("idx_nav_events_ship_date", "ship_id", "start_date"),
    )
    
    @property
    def total_fuel_consumed(self) -> float:
        """Calcula consumo total de combustível do evento."""
        return sum(fc.consumed_quantity for fc in self.fuel_consumption)
