"""
Modelo de Consumo de Combustível.

Registra consumo de combustível por evento de navegação.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.navigation_event import NavigationEvent


class FuelConsumption(Base, UUIDMixin):
    """
    Registro de consumo de combustível.
    
    Associado a um evento de navegação, registra quantidade
    consumida e tipo de combustível.
    
    Attributes:
        id: UUID único do registro
        session_id: ID da sessão de navegação
        consumed_quantity: Quantidade consumida em toneladas
        fuel_type: Tipo de combustível (ex: "LSHFO 0.5")
        created_at: Data de criação do registro
    """
    
    __tablename__ = "fuel_consumption"
    
    # Referência à sessão de navegação
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("navigation_events.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Consumo
    consumed_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    # Tipo de combustível
    fuel_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relacionamento
    navigation_event: Mapped["NavigationEvent"] = relationship(
        "NavigationEvent",
        back_populates="fuel_consumption"
    )
