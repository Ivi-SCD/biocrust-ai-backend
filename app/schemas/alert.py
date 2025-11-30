"""
Schemas para Alertas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertSeverityEnum:
    """Severidades de alerta."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatusEnum:
    """Status de alerta."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class RecommendedAction(BaseModel):
    """Ação recomendada para um alerta."""
    
    action: str = Field(..., description="Ação a tomar")
    urgency: str = Field(..., description="Urgência: immediate, high, medium, low")
    estimated_cost: Optional[float] = Field(default=None, description="Custo estimado")
    estimated_savings: Optional[float] = Field(default=None, description="Economia estimada")
    potential_reduction: Optional[str] = Field(default=None, description="Redução potencial")


class AlertDetails(BaseModel):
    """Detalhes específicos do alerta."""
    
    current_index: Optional[float] = Field(default=None, description="Índice atual")
    normam_level: Optional[int] = Field(default=None, description="Nível NORMAM")
    days_since_cleaning: Optional[int] = Field(default=None, description="Dias desde limpeza")
    estimated_additional_cost_per_day: Optional[float] = Field(
        default=None, description="Custo adicional por dia"
    )
    tropical_hours_30d: Optional[float] = Field(default=None, description="Horas tropicais 30d")
    total_hours_30d: Optional[float] = Field(default=None, description="Total horas 30d")
    percentage: Optional[float] = Field(default=None, description="Percentual")
    expected_acceleration: Optional[float] = Field(default=None, description="Aceleração esperada")


class AlertResponse(BaseModel):
    """Resposta de alerta."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="UUID do alerta")
    ship_id: str = Field(..., description="UUID do navio")
    ship_name: str = Field(..., description="Nome do navio")
    severity: str = Field(..., description="Severidade")
    alert_type: str = Field(..., description="Tipo do alerta", serialization_alias="type")
    title: str = Field(..., description="Título")
    message: str = Field(..., description="Mensagem")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detalhes")
    recommended_actions: Optional[List[RecommendedAction]] = Field(
        default=None, description="Ações recomendadas"
    )
    created_at: datetime = Field(..., description="Data de criação")
    acknowledged_at: Optional[datetime] = Field(default=None, description="Data de reconhecimento")
    acknowledged_by: Optional[str] = Field(default=None, description="Reconhecido por")
    status: str = Field(..., description="Status")


class AlertListResponse(BaseModel):
    """Resposta para lista de alertas."""
    
    total: int = Field(..., description="Total de alertas")
    alerts: List[AlertResponse] = Field(..., description="Lista de alertas")


class AlertAcknowledgeRequest(BaseModel):
    """Request para reconhecer alerta."""
    
    acknowledged_by: str = Field(..., description="UUID do usuário")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Notas")


class AlertFilterParams(BaseModel):
    """Parâmetros de filtro para alertas."""
    
    severity: Optional[str] = Field(default=None, description="Filtrar por severidade")
    ship_id: Optional[str] = Field(default=None, description="Filtrar por navio")
    status: Optional[str] = Field(default=None, description="Filtrar por status")
    limit: int = Field(default=50, ge=1, le=500, description="Limite")
    offset: int = Field(default=0, ge=0, description="Offset")


class NotificationChannel(BaseModel):
    """Canal de notificação."""
    
    channel_type: str = Field(..., description="Tipo: email, push, sms", serialization_alias="type")
    enabled: bool = Field(default=True, description="Se está habilitado")


class AlertRuleResponse(BaseModel):
    """Resposta de regra de alerta."""
    
    id: str = Field(..., description="UUID da regra")
    name: str = Field(..., description="Nome da regra")
    condition: str = Field(..., description="Condição (expressão)")
    severity: str = Field(..., description="Severidade")
    enabled: bool = Field(..., description="Se está habilitada")
    notification_channels: Optional[List[str]] = Field(
        default=None, description="Canais de notificação"
    )


class AlertRulesListResponse(BaseModel):
    """Lista de regras de alerta."""
    
    rules: List[AlertRuleResponse] = Field(..., description="Lista de regras")
