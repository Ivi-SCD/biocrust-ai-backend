"""
Modelo de Relatório.

Armazena metadados de relatórios gerados.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin, TimestampMixin


class ReportStatus(str, Enum):
    """Status de geração de relatório."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(str, Enum):
    """Tipos de relatório disponíveis."""
    EXECUTIVE_SUMMARY = "executive_summary"
    FLEET_ANALYSIS = "fleet_analysis"
    SHIP_DETAIL = "ship_detail"
    COST_ANALYSIS = "cost_analysis"
    SUSTAINABILITY = "sustainability"


class Report(Base, UUIDMixin, TimestampMixin):
    """
    Relatório gerado pelo sistema.
    
    Armazena metadados e status de relatórios gerados
    assincronamente pelo Celery.
    
    Attributes:
        id: UUID único do relatório
        report_type: Tipo do relatório
        status: Status atual da geração
        progress_pct: Percentual de progresso
        current_step: Etapa atual
        file_path: Caminho do arquivo gerado
        file_size_bytes: Tamanho do arquivo
        download_url: URL para download
        expires_at: Data de expiração
        parameters: Parâmetros usados na geração (JSON)
        error_message: Mensagem de erro se falhou
        requested_by: UUID do usuário que solicitou
    """
    
    __tablename__ = "reports"
    
    # Tipo
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=ReportStatus.PENDING.value,
        nullable=False,
        index=True
    )
    progress_pct: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    current_step: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Arquivo
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True
    )
    download_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    pages: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    # Expiração
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Parâmetros
    parameters: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )
    
    # Erro
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Solicitante
    requested_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True
    )
    
    def set_processing(self, step: str = "Iniciando") -> None:
        """Marca relatório como em processamento."""
        self.status = ReportStatus.PROCESSING.value
        self.current_step = step
    
    def update_progress(self, pct: int, step: str) -> None:
        """Atualiza progresso."""
        self.progress_pct = pct
        self.current_step = step
    
    def set_completed(
        self,
        file_path: str,
        download_url: str,
        file_size: int,
        pages: int,
        expires_at: datetime
    ) -> None:
        """Marca como concluído."""
        self.status = ReportStatus.COMPLETED.value
        self.progress_pct = 100
        self.current_step = "Concluído"
        self.file_path = file_path
        self.download_url = download_url
        self.file_size_bytes = file_size
        self.pages = pages
        self.expires_at = expires_at
    
    def set_failed(self, error: str) -> None:
        """Marca como falho."""
        self.status = ReportStatus.FAILED.value
        self.error_message = error
