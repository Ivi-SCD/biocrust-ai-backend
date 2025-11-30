"""
Schemas para Analytics.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TrendDirection:
    """Direção da tendência."""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"


class FleetAggregate(BaseModel):
    """Agregação da frota."""
    
    current_avg: float = Field(..., description="Média atual")
    previous_period_avg: float = Field(..., description="Média do período anterior")
    change_pct: float = Field(..., description="Variação percentual")
    trend: str = Field(..., description="Tendência: improving, stable, worsening")


class ClassAnalysis(BaseModel):
    """Análise por classe de navio."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    ship_class: str = Field(..., validation_alias="class", serialization_alias="class", description="Classe do navio")
    ship_count: int = Field(..., description="Número de navios")
    avg_index: float = Field(..., description="Índice médio")
    trend: str = Field(..., description="Tendência")
    best_performer: Optional[str] = Field(default=None, description="Melhor navio")
    worst_performer: Optional[str] = Field(default=None, description="Pior navio")


class Correlations(BaseModel):
    """Correlações calculadas."""
    
    tropical_exposure_vs_index: float = Field(..., description="Exposição tropical vs índice")
    avg_speed_vs_index: float = Field(..., description="Velocidade média vs índice")
    days_since_cleaning_vs_index: float = Field(..., description="Dias desde limpeza vs índice")


class Insight(BaseModel):
    """Insight de análise."""
    
    insight_type: str = Field(..., description="Tipo: anomaly, trend, recommendation", serialization_alias="type")
    message: str = Field(..., description="Mensagem")
    severity: str = Field(..., description="Severidade: info, warning, critical")
    investigation_recommended: bool = Field(default=False, description="Se requer investigação")


class FleetTrendsResponse(BaseModel):
    """Resposta de tendências da frota."""
    
    period: str = Field(..., description="Período analisado")
    metric: str = Field(..., description="Métrica analisada")
    fleet_aggregate: FleetAggregate = Field(..., description="Agregação da frota")
    by_class: List[ClassAnalysis] = Field(..., description="Análise por classe")
    correlations: Correlations = Field(..., description="Correlações")
    insights: List[Insight] = Field(default=[], description="Insights")


class FleetTrendsParams(BaseModel):
    """Parâmetros para análise de tendências."""
    
    period: str = Field(
        default="last_30d",
        pattern="^(last_7d|last_30d|last_90d|last_year)$",
        description="Período"
    )
    metric: str = Field(
        default="index",
        pattern="^(index|efficiency|fuel_consumption)$",
        description="Métrica"
    )
    group_by: str = Field(
        default="class",
        pattern="^(class|status)$",
        description="Agrupamento"
    )


class ReferenceShip(BaseModel):
    """Navio de referência para benchmarking."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="UUID do navio")
    name: str = Field(..., description="Nome")
    ship_class: str = Field(..., validation_alias="class", serialization_alias="class", description="Classe")
    current_index: float = Field(..., description="Índice atual", validation_alias="index", serialization_alias="index")


class ComparisonGroup(BaseModel):
    """Grupo de comparação."""
    
    ships_count: int = Field(..., description="Número de navios")
    avg_index: float = Field(..., description="Índice médio")
    median_index: float = Field(..., description="Índice mediano")


class Ranking(BaseModel):
    """Ranking do navio."""
    
    position: int = Field(..., description="Posição no ranking")
    percentile: int = Field(..., description="Percentil")
    interpretation: str = Field(..., description="Interpretação")


class ComparisonFactors(BaseModel):
    """Fatores de comparação."""
    
    better_route_planning: Optional[bool] = Field(default=None, description="Melhor planejamento")
    more_frequent_cleaning: Optional[bool] = Field(default=None, description="Limpeza mais frequente")
    better_operational_efficiency: Optional[bool] = Field(default=None, description="Melhor eficiência")


class ShipComparison(BaseModel):
    """Comparação com outro navio."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    ship_name: str = Field(..., description="Nome do navio")
    ship_index: float = Field(..., description="Índice", validation_alias="index", serialization_alias="index")
    delta: float = Field(..., description="Diferença")
    factors: Optional[ComparisonFactors] = Field(default=None, description="Fatores")


class ImprovementOpportunity(BaseModel):
    """Oportunidade de melhoria."""
    
    area: str = Field(..., description="Área de melhoria")
    potential_improvement_pct: float = Field(..., description="Potencial de melhoria %")
    estimated_value_brl: float = Field(..., description="Valor estimado em R$")


class BenchmarkingRequest(BaseModel):
    """Request para benchmarking."""
    
    ship_id: str = Field(..., description="UUID do navio de referência")
    comparison_group: str = Field(
        default="same_class",
        pattern="^(same_class|same_age|custom_list)$",
        description="Grupo de comparação"
    )
    custom_ship_ids: Optional[List[str]] = Field(
        default=None, description="Lista de navios para comparação customizada"
    )


class BenchmarkingResponse(BaseModel):
    """Resposta de benchmarking."""
    
    reference_ship: ReferenceShip = Field(..., description="Navio de referência")
    comparison_group: ComparisonGroup = Field(..., description="Grupo de comparação")
    ranking: Ranking = Field(..., description="Ranking")
    detailed_comparison: List[ShipComparison] = Field(..., description="Comparação detalhada")
    improvement_opportunities: List[ImprovementOpportunity] = Field(
        ..., description="Oportunidades de melhoria"
    )
