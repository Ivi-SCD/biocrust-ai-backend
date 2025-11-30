"""
Modelo de Índice de Bioincrustação.

Armazena resultados dos cálculos do modelo físico-estatístico.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.ship import Ship


class BiofoulingIndex(Base, UUIDMixin):
    """
    Índice de bioincrustação calculado.
    
    Armazena o resultado do cálculo do modelo físico-estatístico
    para um navio em um dado momento. Configurado como hypertable
    no TimescaleDB para consultas eficientes de séries temporais.
    
    Attributes:
        id: UUID único do registro
        ship_id: UUID do navio
        calculated_at: Data/hora do cálculo
        index_value: Índice de bioincrustação (0-100)
        normam_level: Nível NORMAM estimado (0-4)
        component_efficiency: Componente de eficiência hidrodinâmica
        component_environmental: Componente de exposição ambiental
        component_temporal: Componente temporal
        component_operational: Componente operacional
        calculation_metadata: Metadados adicionais do cálculo (JSON)
    """
    
    __tablename__ = "biofouling_indices"
    
    # Referência ao navio
    ship_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ships.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamp do cálculo
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Índice principal
    index_value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    # Nível NORMAM
    normam_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    # Componentes do índice
    component_efficiency: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    component_environmental: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    component_temporal: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    component_operational: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Metadados adicionais
    calculation_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Nome da coluna no banco mantém "metadata"
        JSONB,
        nullable=True
    )
    
    # Timestamp de criação
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relacionamento
    ship: Mapped["Ship"] = relationship(
        "Ship",
        back_populates="biofouling_indices"
    )
    
    # Índices
    __table_args__ = (
        Index("idx_biofouling_ship_time", "ship_id", "calculated_at"),
        Index("idx_biofouling_calculated_at_desc", calculated_at.desc()),
        # Comentário para criar hypertable após migration:
        # SELECT create_hypertable('biofouling_indices', 'calculated_at');
    )
    
    @property
    def status(self) -> str:
        """
        Retorna status de alerta baseado no nível NORMAM.
        
        Returns:
            str: 'ok', 'warning' ou 'critical'
        """
        if self.normam_level <= 1:
            return "ok"
        elif self.normam_level == 2:
            return "warning"
        else:
            return "critical"
    
    @property
    def components(self) -> dict:
        """
        Retorna componentes como dicionário.
        
        Returns:
            dict: Dicionário com os componentes do índice
        """
        return {
            "efficiency": self.component_efficiency,
            "environmental": self.component_environmental,
            "temporal": self.component_temporal,
            "operational": self.component_operational
        }
