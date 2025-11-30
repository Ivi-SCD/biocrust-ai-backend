"""
Schemas para Previsões.
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ForecastScenarios(BaseModel):
    """Cenários para previsão."""
    
    current_pattern: bool = Field(default=True, description="Manter padrão atual")
    tropical_route: bool = Field(default=False, description="Rota tropical")
    temperate_route: bool = Field(default=False, description="Rota temperada")
    cleaning_at_day: Optional[int] = Field(default=None, ge=0, description="Limpeza no dia N")


class ForecastRequest(BaseModel):
    """Request para previsão."""
    
    ship_id: str = Field(..., description="UUID do navio")
    forecast_days: int = Field(default=90, ge=1, le=365, description="Dias de previsão")
    scenarios: ForecastScenarios = Field(
        default_factory=ForecastScenarios,
        description="Cenários"
    )


class ConfidenceInterval(BaseModel):
    """Intervalo de confiança."""
    
    lower: float = Field(..., description="Limite inferior")
    upper: float = Field(..., description="Limite superior")


class PredictionPoint(BaseModel):
    """Ponto de previsão."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    day: int = Field(..., description="Dia da previsão")
    predicted_index: float = Field(..., description="Índice previsto", validation_alias="index", serialization_alias="index")
    normam_level: int = Field(..., description="Nível NORMAM previsto")
    confidence_interval: Optional[ConfidenceInterval] = Field(
        default=None, description="Intervalo de confiança"
    )


class Milestone(BaseModel):
    """Marco/evento previsto."""
    
    event: str = Field(..., description="Evento")
    estimated_day: int = Field(..., description="Dia estimado")
    estimated_date: date = Field(..., description="Data estimada")


class Scenario(BaseModel):
    """Cenário de previsão."""
    
    scenario_name: str = Field(..., description="Nome do cenário")
    description: str = Field(..., description="Descrição")
    predictions: List[PredictionPoint] = Field(..., description="Pontos de previsão")
    milestones: List[Milestone] = Field(default=[], description="Marcos")


class Recommendation(BaseModel):
    """Recomendação baseada na previsão."""
    
    action: str = Field(..., description="Ação recomendada")
    urgency: str = Field(..., description="Urgência: low, medium, high, critical")
    optimal_timing_days: Optional[int] = Field(default=None, description="Timing ótimo em dias")
    reasoning: str = Field(..., description="Justificativa")


class ForecastResponse(BaseModel):
    """Resposta de previsão."""
    
    ship_id: str = Field(..., description="UUID do navio")
    ship_name: str = Field(..., description="Nome do navio")
    current_index: float = Field(..., description="Índice atual")
    forecast_period_days: int = Field(..., description="Período de previsão")
    scenarios: List[Scenario] = Field(..., description="Cenários")
    recommendations: List[Recommendation] = Field(..., description="Recomendações")
