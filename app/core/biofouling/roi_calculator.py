"""
Calculador de ROI para estratégias de manutenção.

Calcula retorno sobre investimento de diferentes estratégias
de limpeza e manutenção de casco.
"""

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

import structlog

from app.config import settings
from app.core.biofouling.predictor import BiofoulingPredictor

logger = structlog.get_logger()


@dataclass
class StrategyCosts:
    """Custos de uma estratégia."""
    cleaning_cost: float
    downtime_cost: float
    additional_fuel_cost: float
    total_cost: float


@dataclass
class StrategySavings:
    """Economias de uma estratégia."""
    fuel_saved_tons: float
    fuel_cost_saved: float
    net_savings: float


@dataclass
class StrategyAnalysis:
    """Análise completa de uma estratégia."""
    name: str
    costs: StrategyCosts
    savings: StrategySavings
    roi_percentage: float
    payback_period_days: Optional[int]
    npv_12_months: float


class ROICalculator:
    """
    Calculador de ROI para estratégias de manutenção.
    
    Considera:
    - Custo de limpeza
    - Custo de parada (downtime)
    - Economia de combustível
    - Valor presente líquido
    - Análise de sensibilidade
    """
    
    # Constantes de referência
    AVG_DAILY_FUEL_CONSUMPTION_TONS = 50  # Toneladas/dia
    OPERATIONAL_DAYS_PER_MONTH = 25
    DISCOUNT_RATE_MONTHLY = 0.01  # 1% ao mês
    
    def __init__(self):
        """Inicializa o calculador."""
        self.predictor = BiofoulingPredictor()
        logger.info("roi_calculator_initialized")
    
    def calculate_strategies(
        self,
        current_index: float,
        strategies: List[Dict],
        fuel_price_per_ton: float = None,
        operational_days_per_year: int = 330,
        downtime_cost_per_day: float = None,
        tropical_exposure_pct: float = 0.5
    ) -> Dict:
        """
        Calcula ROI para múltiplas estratégias de manutenção.
        
        Args:
            current_index: Índice atual de bioincrustação
            strategies: Lista de estratégias a analisar
            fuel_price_per_ton: Preço do combustível em R$
            operational_days_per_year: Dias operacionais por ano
            downtime_cost_per_day: Custo de parada por dia
            tropical_exposure_pct: Exposição a águas tropicais
            
        Returns:
            Dicionário com análises e recomendação
        """
        fuel_price = fuel_price_per_ton or settings.DEFAULT_FUEL_PRICE_PER_TON
        downtime_cost = downtime_cost_per_day or settings.DEFAULT_DOWNTIME_COST_PER_DAY
        
        analyzed = []
        
        # Calcular baseline (não fazer nada)
        baseline_costs = self._calculate_fuel_cost_over_period(
            current_index,
            365,
            fuel_price,
            tropical_exposure_pct
        )
        
        for strategy in strategies:
            analysis = self._analyze_strategy(
                strategy=strategy,
                current_index=current_index,
                baseline_costs=baseline_costs,
                fuel_price=fuel_price,
                downtime_cost=downtime_cost,
                tropical_exposure_pct=tropical_exposure_pct
            )
            analyzed.append(analysis)
        
        # Determinar melhor estratégia
        best = max(analyzed, key=lambda x: x.roi_percentage)
        
        # Análise de sensibilidade
        sensitivity = self._sensitivity_analysis(
            best_strategy=best,
            current_index=current_index,
            strategies=strategies,
            base_fuel_price=fuel_price,
            downtime_cost=downtime_cost,
            tropical_pct=tropical_exposure_pct
        )
        
        return {
            "analyzed_strategies": analyzed,
            "recommendation": {
                "best_strategy": best.name,
                "rationale": self._generate_rationale(best, analyzed),
                "sensitivity_analysis": sensitivity
            }
        }
    
    def _analyze_strategy(
        self,
        strategy: Dict,
        current_index: float,
        baseline_costs: float,
        fuel_price: float,
        downtime_cost: float,
        tropical_exposure_pct: float
    ) -> StrategyAnalysis:
        """
        Analisa uma estratégia específica.
        
        Args:
            strategy: Dados da estratégia
            current_index: Índice atual
            baseline_costs: Custos baseline (não fazer nada)
            fuel_price: Preço do combustível
            downtime_cost: Custo de parada
            tropical_exposure_pct: Exposição tropical
            
        Returns:
            Análise da estratégia
        """
        cleaning_cost = strategy.get(
            "cleaning_cost_brl",
            settings.DEFAULT_CLEANING_COST_BRL
        )
        
        cleaning_date = strategy.get("cleaning_date")
        if isinstance(cleaning_date, str):
            cleaning_date = date.fromisoformat(cleaning_date)
        
        days_until_cleaning = (cleaning_date - date.today()).days
        days_until_cleaning = max(0, days_until_cleaning)
        
        # Custo de downtime (assumir 3 dias de parada)
        downtime_days = settings.DEFAULT_DOWNTIME_DAYS
        downtime_total = downtime_days * downtime_cost
        
        # Custo adicional de combustível até a limpeza
        additional_fuel_cost = self._calculate_fuel_cost_over_period(
            current_index,
            days_until_cleaning,
            fuel_price,
            tropical_exposure_pct
        )
        
        total_cost = cleaning_cost + downtime_total + additional_fuel_cost
        
        # Economia após limpeza (próximos 12 meses)
        if days_until_cleaning <= 30:
            # Limpeza em breve - economia significativa
            savings_period = 365 - days_until_cleaning
            post_cleaning_costs = self._calculate_fuel_cost_over_period(
                5.0,  # Índice pós-limpeza
                savings_period,
                fuel_price,
                tropical_exposure_pct
            )
            
            # Comparar com baseline
            baseline_remaining = self._calculate_fuel_cost_over_period(
                current_index,
                savings_period,
                fuel_price,
                tropical_exposure_pct,
                include_growth=True
            )
            
            fuel_cost_saved = baseline_remaining - post_cleaning_costs
            fuel_saved_tons = fuel_cost_saved / fuel_price
        else:
            # Limpeza tardia - economia menor
            fuel_saved_tons = 0
            fuel_cost_saved = 0
        
        net_savings = fuel_cost_saved - total_cost
        
        # ROI
        roi_pct = (net_savings / total_cost * 100) if total_cost > 0 else 0
        
        # Payback period
        daily_savings = fuel_cost_saved / 365 if fuel_cost_saved > 0 else 0
        payback_days = int(total_cost / daily_savings) if daily_savings > 0 else None
        
        # NPV (12 meses)
        npv = self._calculate_npv(
            investment=total_cost,
            monthly_savings=fuel_cost_saved / 12,
            months=12
        )
        
        return StrategyAnalysis(
            name=strategy.get("name", "unnamed"),
            costs=StrategyCosts(
                cleaning_cost=cleaning_cost,
                downtime_cost=downtime_total,
                additional_fuel_cost=additional_fuel_cost,
                total_cost=total_cost
            ),
            savings=StrategySavings(
                fuel_saved_tons=round(fuel_saved_tons, 1),
                fuel_cost_saved=round(fuel_cost_saved, 2),
                net_savings=round(net_savings, 2)
            ),
            roi_percentage=round(roi_pct, 1),
            payback_period_days=payback_days,
            npv_12_months=round(npv, 2)
        )
    
    def _calculate_fuel_cost_over_period(
        self,
        initial_index: float,
        days: int,
        fuel_price: float,
        tropical_pct: float,
        include_growth: bool = False
    ) -> float:
        """
        Calcula custo adicional de combustível devido à bioincrustação.
        
        Cada 10 pontos de índice = ~3% mais consumo.
        
        Args:
            initial_index: Índice inicial
            days: Período em dias
            fuel_price: Preço do combustível
            tropical_pct: Exposição tropical
            include_growth: Incluir crescimento do índice
            
        Returns:
            Custo adicional em R$
        """
        if days <= 0:
            return 0.0
        
        total_cost = 0.0
        daily_base_consumption = self.AVG_DAILY_FUEL_CONSUMPTION_TONS
        
        # Calcular por períodos de 30 dias para capturar crescimento
        for period_start in range(0, days, 30):
            period_days = min(30, days - period_start)
            
            if include_growth:
                # Prever índice para este período
                period_index = self.predictor._calculate_future_index(
                    initial_index,
                    period_start,
                    tropical_pct
                )
            else:
                period_index = initial_index
            
            # Consumo adicional = baseline + (índice - 20) * 0.3%
            # Assumindo que índice 20 é o limpo
            additional_pct = max(0, (period_index - 20) * 0.003)
            additional_consumption = daily_base_consumption * additional_pct
            
            period_cost = additional_consumption * period_days * fuel_price
            total_cost += period_cost
        
        return total_cost
    
    def _calculate_npv(
        self,
        investment: float,
        monthly_savings: float,
        months: int
    ) -> float:
        """
        Calcula Valor Presente Líquido.
        
        Args:
            investment: Investimento inicial
            monthly_savings: Economia mensal
            months: Número de meses
            
        Returns:
            NPV
        """
        npv = -investment
        
        for month in range(1, months + 1):
            discount_factor = 1 / ((1 + self.DISCOUNT_RATE_MONTHLY) ** month)
            npv += monthly_savings * discount_factor
        
        return npv
    
    def _sensitivity_analysis(
        self,
        best_strategy: StrategyAnalysis,
        current_index: float,
        strategies: List[Dict],
        base_fuel_price: float,
        downtime_cost: float,
        tropical_pct: float
    ) -> Dict:
        """
        Realiza análise de sensibilidade.
        
        Args:
            best_strategy: Melhor estratégia
            current_index: Índice atual
            strategies: Estratégias originais
            base_fuel_price: Preço base de combustível
            downtime_cost: Custo de parada
            tropical_pct: Exposição tropical
            
        Returns:
            Análise de sensibilidade
        """
        best_original = next(
            s for s in strategies if s.get("name") == best_strategy.name
        )
        
        # Variação de preço de combustível
        variations = {}
        
        for label, multiplier in [("minus_20_pct", 0.8), ("plus_20_pct", 1.2)]:
            new_price = base_fuel_price * multiplier
            
            baseline = self._calculate_fuel_cost_over_period(
                current_index, 365, new_price, tropical_pct
            )
            
            analysis = self._analyze_strategy(
                strategy=best_original,
                current_index=current_index,
                baseline_costs=baseline,
                fuel_price=new_price,
                downtime_cost=downtime_cost,
                tropical_exposure_pct=tropical_pct
            )
            
            variations[label] = {"roi": analysis.roi_percentage}
        
        return {
            "fuel_price_variation": variations
        }
    
    def _generate_rationale(
        self,
        best: StrategyAnalysis,
        all_strategies: List[StrategyAnalysis]
    ) -> str:
        """
        Gera justificativa para a recomendação.
        
        Args:
            best: Melhor estratégia
            all_strategies: Todas as estratégias
            
        Returns:
            Texto de justificativa
        """
        parts = []
        
        if best.roi_percentage > 0:
            parts.append(f"ROI positivo de {best.roi_percentage}%")
        
        if best.payback_period_days and best.payback_period_days < 60:
            parts.append(f"payback em {best.payback_period_days} dias")
        
        if best.npv_12_months > 0:
            parts.append(f"VPL de R$ {best.npv_12_months:,.0f} em 12 meses")
        
        # Comparar com outras estratégias
        worse_strategies = [s for s in all_strategies if s.name != best.name and s.roi_percentage < best.roi_percentage]
        if worse_strategies:
            avg_other_roi = sum(s.roi_percentage for s in worse_strategies) / len(worse_strategies)
            parts.append(f"ROI {best.roi_percentage - avg_other_roi:.1f}% melhor que alternativas")
        
        if parts:
            return ". ".join(parts) + "."
        else:
            return "Melhor opção disponível baseado nos parâmetros fornecidos."
