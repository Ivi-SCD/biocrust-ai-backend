"""
Schemas para Cálculo de ROI.
"""

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CleaningStrategy(BaseModel):
    """Estratégia de limpeza."""
    
    name: str = Field(..., description="Nome da estratégia")
    cleaning_date: date = Field(..., description="Data da limpeza")
    cleaning_cost_brl: float = Field(
        default=85000, ge=0, description="Custo de limpeza em R$"
    )


class ROICalculateRequest(BaseModel):
    """Request para cálculo de ROI."""
    
    ship_id: str = Field(..., description="UUID do navio")
    strategies: List[CleaningStrategy] = Field(
        ..., min_length=1, max_length=10, description="Estratégias a analisar"
    )
    fuel_price_per_ton: float = Field(
        default=4200, ge=0, description="Preço do combustível por tonelada em R$"
    )
    operational_days_per_year: int = Field(
        default=330, ge=1, le=365, description="Dias operacionais por ano"
    )
    downtime_cost_per_day: float = Field(
        default=120000, ge=0, description="Custo de parada por dia em R$"
    )


class StrategyCosts(BaseModel):
    """Custos de uma estratégia."""
    
    cleaning_cost: float = Field(..., description="Custo de limpeza")
    downtime_cost: float = Field(..., description="Custo de parada")
    additional_fuel_cost: float = Field(..., description="Custo adicional de combustível")
    total_cost: float = Field(..., description="Custo total")


class StrategySavings(BaseModel):
    """Economias de uma estratégia."""
    
    fuel_saved_tons: float = Field(..., description="Combustível economizado em toneladas")
    fuel_cost_saved: float = Field(..., description="Custo de combustível economizado")
    net_savings: float = Field(..., description="Economia líquida")


class StrategyAnalysis(BaseModel):
    """Análise de uma estratégia."""
    
    name: str = Field(..., description="Nome da estratégia")
    costs: StrategyCosts = Field(..., description="Custos")
    savings: StrategySavings = Field(..., description="Economias")
    roi_percentage: float = Field(..., description="ROI em percentual")
    payback_period_days: Optional[int] = Field(default=None, description="Período de payback")
    npv_12_months: float = Field(..., description="VPL em 12 meses")


class FuelPriceVariation(BaseModel):
    """Variação de preço de combustível."""
    
    roi: float = Field(..., description="ROI com variação")


class SensitivityAnalysis(BaseModel):
    """Análise de sensibilidade."""
    
    fuel_price_variation: Dict[str, FuelPriceVariation] = Field(
        ..., description="Variações de preço de combustível"
    )


class ROIRecommendation(BaseModel):
    """Recomendação de ROI."""
    
    best_strategy: str = Field(..., description="Melhor estratégia")
    rationale: str = Field(..., description="Justificativa")
    sensitivity_analysis: SensitivityAnalysis = Field(
        ..., description="Análise de sensibilidade"
    )


class ROICalculateResponse(BaseModel):
    """Resposta do cálculo de ROI."""
    
    ship_id: str = Field(..., description="UUID do navio")
    ship_name: str = Field(..., description="Nome do navio")
    current_index: float = Field(..., description="Índice atual")
    analyzed_strategies: List[StrategyAnalysis] = Field(
        ..., description="Estratégias analisadas"
    )
    recommendation: ROIRecommendation = Field(..., description="Recomendação")
