"""
Modelo de Posição AIS.

Dados de rastreamento em tempo real via Sistema de Identificação Automática.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.ship import Ship


class AISPosition(Base, UUIDMixin):
    """
    Posição AIS de um navio.
    
    Armazena dados de rastreamento em tempo real.
    Tabela configurada como hypertable no TimescaleDB para
    otimização de séries temporais.
    
    Attributes:
        id: UUID único da posição
        ship_id: UUID do navio
        timestamp: Data/hora da posição (timezone-aware)
        latitude: Latitude em graus decimais
        longitude: Longitude em graus decimais
        speed: Velocidade em nós
        heading: Rumo em graus
        created_at: Data de inserção no banco
    """
    
    __tablename__ = "ais_positions"
    
    # Referência ao navio
    ship_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ships.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamp da posição
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Coordenadas
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    # Dados de navegação
    speed: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )
    heading: Mapped[float] = mapped_column(
        Float,
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
        back_populates="positions"
    )
    
    # Índices compostos para queries comuns
    __table_args__ = (
        Index("idx_ais_positions_ship_time", "ship_id", "timestamp"),
        Index("idx_ais_positions_timestamp_desc", timestamp.desc()),
        # Comentário para criar hypertable após migration:
        # SELECT create_hypertable('ais_positions', 'timestamp');
    )
    
    @property
    def water_type(self) -> str:
        """
        Classifica o tipo de água baseado na latitude.
        
        Returns:
            str: 'tropical', 'subtropical' ou 'temperate'
        """
        abs_lat = abs(self.latitude)
        if abs_lat < 20:
            return "tropical"
        elif abs_lat < 35:
            return "subtropical"
        else:
            return "temperate"
