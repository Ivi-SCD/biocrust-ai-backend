"""
Modelo de Navio (Ship).

Define a entidade principal de navios da frota.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, Float, Integer, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.ais_position import AISPosition
    from app.models.navigation_event import NavigationEvent
    from app.models.inspection import Inspection
    from app.models.biofouling_index import BiofoulingIndex
    from app.models.alert import Alert


class Ship(Base, UUIDMixin, TimestampMixin):
    """
    Modelo de navio da frota Transpetro.
    
    Attributes:
        id: UUID único do navio
        name: Nome do navio (único)
        ship_class: Classe do navio (Aframax, Suezmax, etc.)
        ship_type: Tipo do navio
        gross_tonnage: Porte bruto em toneladas
        length_m: Comprimento total em metros
        beam_m: Boca (largura) em metros
        draft_m: Calado em metros
        last_cleaning_date: Data da última limpeza
        created_at: Data de criação do registro
        updated_at: Data da última atualização
    """
    
    __tablename__ = "ships"
    
    # Identificação
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Classificação
    ship_class: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    ship_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Especificações técnicas
    gross_tonnage: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    length_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    beam_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    draft_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Manutenção
    last_cleaning_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    
    # Relacionamentos
    positions: Mapped[List["AISPosition"]] = relationship(
        "AISPosition",
        back_populates="ship",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    events: Mapped[List["NavigationEvent"]] = relationship(
        "NavigationEvent",
        back_populates="ship",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    inspections: Mapped[List["Inspection"]] = relationship(
        "Inspection",
        back_populates="ship",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    biofouling_indices: Mapped[List["BiofoulingIndex"]] = relationship(
        "BiofoulingIndex",
        back_populates="ship",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="ship",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    environmental_metrics: Mapped[Optional["ShipEnvironmentalMetrics"]] = relationship(
        "ShipEnvironmentalMetrics",
        back_populates="ship",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Índices
    __table_args__ = (
        Index("idx_ships_class_name", "ship_class", "name"),
    )
    
    @property
    def days_since_cleaning(self) -> Optional[int]:
        """Calcula dias desde a última limpeza."""
        if self.last_cleaning_date is None:
            return None
        return (date.today() - self.last_cleaning_date).days


class ShipEnvironmentalMetrics(Base, TimestampMixin):
    """
    Métricas ambientais agregadas do navio.
    
    Cache de exposição a diferentes tipos de água para
    cálculos de bioincrustação.
    
    Attributes:
        ship_id: UUID do navio (PK e FK)
        period_start: Início do período de análise
        period_end: Fim do período de análise
        tropical_hours: Horas em águas tropicais
        subtropical_hours: Horas em águas subtropicais
        temperate_hours: Horas em águas temperadas
    """
    
    __tablename__ = "ship_environmental_metrics"
    
    ship_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ships.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    
    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    
    tropical_hours: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    subtropical_hours: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    temperate_hours: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    
    # Relacionamento
    ship: Mapped["Ship"] = relationship(
        "Ship",
        back_populates="environmental_metrics"
    )
    
    @property
    def total_hours(self) -> float:
        """Total de horas no período."""
        return self.tropical_hours + self.subtropical_hours + self.temperate_hours
    
    @property
    def tropical_percentage(self) -> float:
        """Percentual de tempo em águas tropicais."""
        total = self.total_hours
        if total == 0:
            return 0.0
        return (self.tropical_hours / total) * 100
