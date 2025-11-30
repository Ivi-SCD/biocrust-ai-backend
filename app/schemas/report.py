"""
Schemas para Relatórios.
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportPeriod(BaseModel):
    """Período do relatório."""
    
    start: date = Field(..., description="Data inicial")
    end: date = Field(..., description="Data final")


class ReportScope(BaseModel):
    """Escopo do relatório."""
    
    ships: List[str] = Field(default=["all"], description="Navios ou 'all'")
    classes: Optional[List[str]] = Field(default=None, description="Classes de navios")


class ReportGenerateRequest(BaseModel):
    """Request para gerar relatório."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    report_type: str = Field(
        ...,
        pattern="^(executive_summary|fleet_analysis|ship_detail|cost_analysis|sustainability)$",
        description="Tipo do relatório",
        validation_alias="type",
        serialization_alias="type"
    )
    period: ReportPeriod = Field(..., description="Período")
    scope: ReportScope = Field(default_factory=ReportScope, description="Escopo")
    sections: List[str] = Field(
        default=[
            "fleet_overview",
            "top_performers",
            "critical_situations",
            "cost_analysis",
            "recommendations"
        ],
        description="Seções do relatório"
    )
    format: str = Field(
        default="pdf",
        pattern="^(pdf|xlsx|html)$",
        description="Formato"
    )
    language: str = Field(default="pt-BR", description="Idioma")
    recipient_email: Optional[str] = Field(default=None, description="E-mail do destinatário")


class ReportGenerateResponse(BaseModel):
    """Resposta da solicitação de relatório."""
    
    report_id: str = Field(..., description="UUID do relatório")
    status: str = Field(..., description="Status")
    estimated_completion: datetime = Field(..., description="Conclusão estimada")
    webhook_url: Optional[str] = Field(default=None, description="URL do webhook")


class ReportMetadata(BaseModel):
    """Metadados do relatório."""
    
    pages: int = Field(..., description="Número de páginas")
    generated_at: datetime = Field(..., description="Data de geração")
    file_size_bytes: int = Field(..., description="Tamanho do arquivo")


class ReportStatusResponse(BaseModel):
    """Resposta de status do relatório."""
    
    report_id: str = Field(..., description="UUID do relatório")
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    progress_pct: Optional[int] = Field(default=None, description="Progresso")
    current_step: Optional[str] = Field(default=None, description="Etapa atual")
    download_url: Optional[str] = Field(default=None, description="URL de download")
    expires_at: Optional[datetime] = Field(default=None, description="Expiração")
    metadata: Optional[ReportMetadata] = Field(default=None, description="Metadados")
    error_message: Optional[str] = Field(default=None, description="Mensagem de erro")
