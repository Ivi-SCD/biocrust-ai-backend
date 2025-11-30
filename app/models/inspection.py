"""
Modelo de Inspeção.

Registra inspeções de casco e verificações de bioincrustação.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Integer, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.ship import Ship


class Inspection(Base, UUIDMixin, TimestampMixin):
    """
    Inspeção de casco do navio.
    
    Registra dados de inspeções presenciais que servem como
    ground truth para validação do modelo de bioincrustação.
    
    Attributes:
        id: UUID único da inspeção
        ship_id: UUID do navio inspecionado
        inspection_date: Data da inspeção
        location: Local da inspeção
        normam_level_confirmed: Nível NORMAM confirmado (0-4)
        hull_condition_pct: Condição do casco em percentual
        fouling_type: Tipo de incrustação encontrada
        notes: Observações adicionais
        inspector_name: Nome do inspetor
    """
    
    __tablename__ = "inspections"
    
    # Referência ao navio
    ship_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ships.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Data e local
    inspection_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Resultado da inspeção
    normam_level_confirmed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    hull_condition_pct: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    fouling_type: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Metadados
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    inspector_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Relacionamento
    ship: Mapped["Ship"] = relationship(
        "Ship",
        back_populates="inspections"
    )
    
    # Índices
    __table_args__ = (
        Index("idx_inspections_ship_date", "ship_id", "inspection_date"),
    )
