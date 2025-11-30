"""
Modelo de Alerta.

Sistema de alertas inteligentes para bioincrustação.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.ship import Ship


class AlertSeverity(str, Enum):
    """Níveis de severidade de alerta."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status de um alerta."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertType(str, Enum):
    """Tipos de alerta."""
    CRITICAL_LEVEL_REACHED = "critical_level_reached"
    APPROACHING_CRITICAL = "approaching_critical"
    TROPICAL_EXPOSURE_HIGH = "tropical_exposure_high"
    DEGRADATION_ANOMALY = "degradation_anomaly"
    INSPECTION_OVERDUE = "inspection_overdue"
    CLEANING_RECOMMENDED = "cleaning_recommended"


class Alert(Base, UUIDMixin, TimestampMixin):
    """
    Alerta de bioincrustação.
    
    Representa um alerta gerado pelo sistema com base nas
    regras de negócio e análise dos dados de bioincrustação.
    
    Attributes:
        id: UUID único do alerta
        ship_id: UUID do navio relacionado
        severity: Severidade (info, warning, critical)
        alert_type: Tipo do alerta
        title: Título curto do alerta
        message: Mensagem detalhada
        details: Detalhes adicionais (JSON)
        recommended_actions: Ações recomendadas (JSON)
        status: Status atual (active, acknowledged, resolved)
        acknowledged_at: Data/hora do reconhecimento
        acknowledged_by: UUID do usuário que reconheceu
        acknowledged_notes: Notas do reconhecimento
        resolved_at: Data/hora da resolução
    """
    
    __tablename__ = "alerts"
    
    # Referência ao navio
    ship_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ships.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Classificação
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # Conteúdo
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Detalhes adicionais
    details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )
    recommended_actions: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True
    )
    
    # Status e workflow
    status: Mapped[str] = mapped_column(
        String(20),
        default=AlertStatus.ACTIVE.value,
        nullable=False,
        index=True
    )
    
    # Reconhecimento
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True
    )
    acknowledged_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Resolução
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relacionamento
    ship: Mapped["Ship"] = relationship(
        "Ship",
        back_populates="alerts"
    )
    
    # Índices
    __table_args__ = (
        Index("idx_alerts_ship_status", "ship_id", "status", "created_at"),
        Index("idx_alerts_severity_status", "severity", "status"),
    )
    
    def acknowledge(self, user_id: str, notes: Optional[str] = None) -> None:
        """
        Marca o alerta como reconhecido.
        
        Args:
            user_id: UUID do usuário que reconhece
            notes: Notas opcionais
        """
        self.status = AlertStatus.ACKNOWLEDGED.value
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
        self.acknowledged_notes = notes
    
    def resolve(self) -> None:
        """Marca o alerta como resolvido."""
        self.status = AlertStatus.RESOLVED.value
        self.resolved_at = datetime.utcnow()
