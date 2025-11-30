"""
Schemas para cálculo de bioincrustação.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ship import BiofoulingComponents, ShipStatus


class BiofoulingEventInput(BaseModel):
    """Evento de navegação para cálculo de bioincrustação."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    ship_name: str = Field(..., min_length=1, description="Nome do navio")
    start_date: datetime = Field(..., description="Data/hora de início")
    end_date: datetime = Field(..., description="Data/hora de fim")
    distance_nm: float = Field(..., ge=0, description="Distância em milhas náuticas")
    duration_hours: float = Field(..., ge=0, description="Duração em horas")
    speed: float = Field(..., ge=0, description="Velocidade em nós")
    displacement: float = Field(..., ge=0, description="Deslocamento em toneladas")
    aft_draft: float = Field(..., ge=0, description="Calado à ré em metros")
    fwd_draft: float = Field(..., ge=0, description="Calado a vante em metros")
    trim: float = Field(..., description="Trim em metros")
    beaufort_scale: int = Field(..., ge=0, le=12, description="Escala Beaufort")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    mid_draft: Optional[float] = Field(default=None, description="Calado a meia-nau")
    sea_condition: Optional[str] = Field(default=None, description="Condição do mar")


class BiofoulingCalculateRequest(BaseModel):
    """Request para cálculo de bioincrustação."""
    
    events: List[BiofoulingEventInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Lista de eventos para calcular"
    )
    ship_length_m: Optional[float] = Field(
        default=None,
        ge=0,
        description="Comprimento do navio (override)"
    )


class EfficiencyMetrics(BaseModel):
    """Métricas de eficiência."""
    
    nm_per_ton: float = Field(..., description="Milhas por tonelada")
    baseline_nm_per_ton: float = Field(..., description="Baseline de milhas por tonelada")
    degradation_pct: float = Field(..., description="Percentual de degradação")


class BiofoulingResult(BaseModel):
    """Resultado de cálculo para um evento."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    event_index: int = Field(..., description="Índice do evento na lista")
    ship_name: str = Field(..., description="Nome do navio")
    biofouling_index: float = Field(..., ge=0, le=100, description="Índice de bioincrustação", validation_alias="index", serialization_alias="index")
    normam_level: int = Field(..., ge=0, le=4, description="Nível NORMAM")
    status: ShipStatus = Field(..., description="Status")
    components: BiofoulingComponents = Field(..., description="Componentes do índice")
    efficiency_metrics: Optional[EfficiencyMetrics] = Field(
        default=None, description="Métricas de eficiência"
    )
    calculated_at: datetime = Field(..., description="Data do cálculo")


class BiofoulingCalculateResponse(BaseModel):
    """Resposta do cálculo de bioincrustação."""
    
    results: List[BiofoulingResult] = Field(..., description="Resultados dos cálculos")


class StatusDistribution(BaseModel):
    """Distribuição por status."""
    
    ok: int = Field(default=0, description="Navios OK")
    warning: int = Field(default=0, description="Navios em alerta")
    critical: int = Field(default=0, description="Navios críticos")


class LevelDistribution(BaseModel):
    """Distribuição por nível NORMAM."""
    
    level_0: int = Field(default=0, description="Nível 0")
    level_1: int = Field(default=0, description="Nível 1")
    level_2: int = Field(default=0, description="Nível 2")
    level_3: int = Field(default=0, description="Nível 3")
    level_4: int = Field(default=0, description="Nível 4")


class ShipSummary(BaseModel):
    """Resumo de um navio."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., description="Nome do navio")
    biofouling_index: float = Field(..., description="Índice de bioincrustação", validation_alias="index", serialization_alias="index")
    level: int = Field(..., description="Nível NORMAM")
    days_since_cleaning: Optional[int] = Field(default=None, description="Dias desde limpeza")


class MonthlyCostImpact(BaseModel):
    """Impacto de custo mensal."""
    
    additional_fuel_cost_brl: float = Field(..., description="Custo adicional de combustível")
    potential_savings_brl: float = Field(..., description="Economia potencial")


class FleetSummaryResponse(BaseModel):
    """Resumo executivo da frota."""
    
    timestamp: datetime = Field(..., description="Timestamp do resumo")
    total_ships: int = Field(..., description="Total de navios")
    status_distribution: StatusDistribution = Field(..., description="Distribuição por status")
    level_distribution: LevelDistribution = Field(..., description="Distribuição por nível")
    average_index: float = Field(..., description="Índice médio da frota")
    worst_ships: List[ShipSummary] = Field(..., description="Piores navios")
    best_ships: List[ShipSummary] = Field(..., description="Melhores navios")
    monthly_cost_impact: MonthlyCostImpact = Field(..., description="Impacto de custo")
