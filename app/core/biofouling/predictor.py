"""
Previsão temporal de bioincrustação.

Implementa modelo de crescimento não-linear para prever evolução
do índice de bioincrustação ao longo do tempo.
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import structlog

from app.config import settings

logger = structlog.get_logger()


@dataclass
class PredictionPoint:
    """Ponto de previsão."""
    day: int
    index: float
    normam_level: int
    confidence_lower: float
    confidence_upper: float


@dataclass
class Milestone:
    """Marco previsto."""
    event: str
    day: int
    estimated_date: date


@dataclass
class Scenario:
    """Cenário de previsão."""
    name: str
    description: str
    predictions: List[PredictionPoint]
    milestones: List[Milestone]


class BiofoulingPredictor:
    """
    Previsor de evolução de bioincrustação.
    
    Usa modelo de crescimento não-linear baseado em:
    - IMO Guidelines for biofouling management (MEPC.207(62))
    - Schultz (2007) research data
    - Townsin (2003) ship hull fouling penalty
    """
    
    # Taxas de crescimento por tipo de água (índice/mês)
    GROWTH_RATES = {
        "tropical": 12.0,     # Crescimento rápido
        "subtropical": 8.0,   # Crescimento moderado
        "temperate": 5.0,     # Crescimento lento
    }
    
    # Limites de nível NORMAM
    NORMAM_THRESHOLDS = [0, 20, 35, 55, 75, 100]
    
    def __init__(self):
        """Inicializa o previsor."""
        logger.info("biofouling_predictor_initialized")
    
    def predict(
        self,
        current_index: float,
        forecast_days: int,
        tropical_exposure_pct: float = 0.5,
        include_scenarios: Dict[str, bool] = None
    ) -> Dict:
        """
        Gera previsão de evolução do índice.
        
        Args:
            current_index: Índice atual de bioincrustação (0-100)
            forecast_days: Dias para previsão
            tropical_exposure_pct: Percentual de exposição a águas tropicais
            include_scenarios: Cenários a incluir
            
        Returns:
            Dicionário com previsões e recomendações
        """
        include_scenarios = include_scenarios or {
            "current_pattern": True,
            "tropical_route": True,
            "temperate_route": True,
        }
        
        scenarios = []
        
        if include_scenarios.get("current_pattern"):
            scenarios.append(self._predict_scenario(
                "current_pattern",
                "Mantendo padrão operacional atual",
                current_index,
                forecast_days,
                tropical_exposure_pct
            ))
        
        if include_scenarios.get("tropical_route"):
            scenarios.append(self._predict_scenario(
                "tropical_route",
                "Rotas predominantemente tropicais (lat < 20°)",
                current_index,
                forecast_days,
                0.8  # 80% tropical
            ))
        
        if include_scenarios.get("temperate_route"):
            scenarios.append(self._predict_scenario(
                "temperate_route",
                "Rotas predominantemente temperadas (lat > 35°)",
                current_index,
                forecast_days,
                0.2  # 20% tropical
            ))
        
        cleaning_day = include_scenarios.get("cleaning_at_day")
        if cleaning_day is not None:
            scenarios.append(self._predict_cleaning_scenario(
                current_index,
                forecast_days,
                cleaning_day,
                tropical_exposure_pct
            ))
        
        recommendations = self._generate_recommendations(
            current_index,
            scenarios,
            forecast_days
        )
        
        return {
            "scenarios": scenarios,
            "recommendations": recommendations
        }
    
    def _predict_scenario(
        self,
        name: str,
        description: str,
        current_index: float,
        forecast_days: int,
        tropical_pct: float
    ) -> Scenario:
        """
        Gera previsão para um cenário específico.
        
        Args:
            name: Nome do cenário
            description: Descrição
            current_index: Índice atual
            forecast_days: Dias de previsão
            tropical_pct: Percentual de exposição tropical
            
        Returns:
            Cenário com previsões
        """
        predictions = []
        milestones = []
        
        # Calcular pontos de previsão
        prediction_days = [0, 7, 14, 30, 60, 90, 120, 180, 365]
        prediction_days = [d for d in prediction_days if d <= forecast_days]
        
        if forecast_days not in prediction_days:
            prediction_days.append(forecast_days)
        
        prediction_days.sort()
        
        level_milestones_found = set()
        
        for day in prediction_days:
            predicted_index = self._calculate_future_index(
                current_index,
                day,
                tropical_pct
            )
            
            normam_level = self._index_to_normam(predicted_index)
            confidence = self._calculate_confidence(day)
            
            predictions.append(PredictionPoint(
                day=day,
                index=round(predicted_index, 1),
                normam_level=normam_level,
                confidence_lower=round(predicted_index - confidence, 1),
                confidence_upper=round(predicted_index + confidence, 1)
            ))
            
            # Verificar milestones
            if normam_level >= 4 and 4 not in level_milestones_found:
                level_milestones_found.add(4)
                estimated_day = self._estimate_day_for_level(
                    current_index, 4, tropical_pct
                )
                if estimated_day <= forecast_days:
                    milestones.append(Milestone(
                        event="reaches_level_4",
                        day=estimated_day,
                        estimated_date=date.today() + timedelta(days=estimated_day)
                    ))
            
            if normam_level >= 3 and 3 not in level_milestones_found:
                level_milestones_found.add(3)
                estimated_day = self._estimate_day_for_level(
                    current_index, 3, tropical_pct
                )
                if estimated_day <= forecast_days:
                    milestones.append(Milestone(
                        event="reaches_level_3",
                        day=estimated_day,
                        estimated_date=date.today() + timedelta(days=estimated_day)
                    ))
        
        return Scenario(
            name=name,
            description=description,
            predictions=predictions,
            milestones=sorted(milestones, key=lambda m: m.day)
        )
    
    def _predict_cleaning_scenario(
        self,
        current_index: float,
        forecast_days: int,
        cleaning_day: int,
        tropical_pct: float
    ) -> Scenario:
        """
        Gera previsão para cenário com limpeza.
        
        Args:
            current_index: Índice atual
            forecast_days: Dias de previsão
            cleaning_day: Dia da limpeza
            tropical_pct: Exposição tropical
            
        Returns:
            Cenário com limpeza
        """
        predictions = []
        
        # Antes da limpeza
        for day in range(0, min(cleaning_day + 1, forecast_days + 1), 7):
            if day <= cleaning_day:
                predicted = self._calculate_future_index(
                    current_index, day, tropical_pct
                )
            else:
                # Após limpeza - índice reseta para 5 e cresce novamente
                days_after = day - cleaning_day
                predicted = self._calculate_future_index(
                    5.0, days_after, tropical_pct
                )
            
            predictions.append(PredictionPoint(
                day=day,
                index=round(predicted, 1),
                normam_level=self._index_to_normam(predicted),
                confidence_lower=round(predicted - 3, 1),
                confidence_upper=round(predicted + 3, 1)
            ))
        
        # No dia da limpeza
        if cleaning_day <= forecast_days and cleaning_day not in [p.day for p in predictions]:
            predictions.append(PredictionPoint(
                day=cleaning_day,
                index=5.0,
                normam_level=0,
                confidence_lower=3.0,
                confidence_upper=10.0
            ))
        
        # Após limpeza
        for day in range(cleaning_day + 30, forecast_days + 1, 30):
            days_after = day - cleaning_day
            predicted = self._calculate_future_index(
                5.0, days_after, tropical_pct
            )
            
            predictions.append(PredictionPoint(
                day=day,
                index=round(predicted, 1),
                normam_level=self._index_to_normam(predicted),
                confidence_lower=round(predicted - 5, 1),
                confidence_upper=round(predicted + 5, 1)
            ))
        
        predictions.sort(key=lambda p: p.day)
        
        return Scenario(
            name="cleaning_at_day",
            description=f"Limpeza realizada no dia {cleaning_day}",
            predictions=predictions,
            milestones=[Milestone(
                event="cleaning_performed",
                day=cleaning_day,
                estimated_date=date.today() + timedelta(days=cleaning_day)
            )]
        )
    
    def _calculate_future_index(
        self,
        current_index: float,
        days_ahead: int,
        tropical_pct: float
    ) -> float:
        """
        Calcula índice futuro usando modelo de crescimento.
        
        Modelo: crescimento logarítmico com fator de exposição tropical.
        
        Args:
            current_index: Índice atual
            days_ahead: Dias no futuro
            tropical_pct: Exposição tropical (0-1)
            
        Returns:
            Índice previsto
        """
        if days_ahead <= 0:
            return current_index
        
        # Taxa base de crescimento (índice/mês)
        base_rate = 8.0
        
        # Fator de aceleração em águas tropicais
        # Cada 10% de exposição tropical adiciona 15% na taxa
        tropical_factor = 1 + (tropical_pct * 1.5)
        
        # Curva logarítmica (crescimento rápido inicial, depois satura)
        months = days_ahead / 30
        growth = base_rate * tropical_factor * math.log1p(months)
        
        # Fator de saturação (cresce mais devagar quando já está alto)
        saturation_factor = 1 - (current_index / 200)
        growth *= max(0.3, saturation_factor)
        
        predicted = current_index + growth
        
        # Saturar em 100
        return min(100, max(0, predicted))
    
    def _index_to_normam(self, index: float) -> int:
        """Converte índice para nível NORMAM."""
        if index < 20:
            return 0
        elif index < 35:
            return 1
        elif index < 55:
            return 2
        elif index < 75:
            return 3
        else:
            return 4
    
    def _calculate_confidence(self, days: int) -> float:
        """
        Calcula intervalo de confiança baseado no horizonte.
        
        Args:
            days: Dias de previsão
            
        Returns:
            Intervalo de confiança (+/-)
        """
        # Confiança diminui com o tempo
        base_confidence = 3.0
        growth = math.log1p(days / 30) * 2
        return base_confidence + growth
    
    def _estimate_day_for_level(
        self,
        current_index: float,
        target_level: int,
        tropical_pct: float
    ) -> int:
        """
        Estima em quantos dias atingirá um nível NORMAM.
        
        Args:
            current_index: Índice atual
            target_level: Nível NORMAM alvo
            tropical_pct: Exposição tropical
            
        Returns:
            Dias estimados
        """
        target_index = self.NORMAM_THRESHOLDS[target_level]
        
        if current_index >= target_index:
            return 0
        
        # Busca binária para encontrar o dia
        low, high = 0, 365
        
        while low < high:
            mid = (low + high) // 2
            predicted = self._calculate_future_index(
                current_index, mid, tropical_pct
            )
            
            if predicted < target_index:
                low = mid + 1
            else:
                high = mid
        
        return low
    
    def _generate_recommendations(
        self,
        current_index: float,
        scenarios: List[Scenario],
        forecast_days: int
    ) -> List[Dict]:
        """
        Gera recomendações baseadas nas previsões.
        
        Args:
            current_index: Índice atual
            scenarios: Cenários previstos
            forecast_days: Período de previsão
            
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        current_level = self._index_to_normam(current_index)
        
        # Encontrar cenário base
        base_scenario = next(
            (s for s in scenarios if s.name == "current_pattern"),
            scenarios[0] if scenarios else None
        )
        
        if not base_scenario:
            return recommendations
        
        # Verificar se vai atingir nível crítico
        level_4_milestone = next(
            (m for m in base_scenario.milestones if m.event == "reaches_level_4"),
            None
        )
        
        if level_4_milestone and level_4_milestone.day <= forecast_days:
            # Recomendar limpeza antes de atingir nível crítico
            optimal_day = max(0, level_4_milestone.day - 3)
            recommendations.append({
                "action": "schedule_cleaning",
                "urgency": "high" if level_4_milestone.day <= 30 else "medium",
                "optimal_timing_days": optimal_day,
                "reasoning": f"Limpeza antes do dia {level_4_milestone.day} evita atingir nível crítico"
            })
        
        # Se já está em nível 3+
        if current_level >= 3:
            recommendations.append({
                "action": "immediate_cleaning",
                "urgency": "critical" if current_level >= 4 else "high",
                "optimal_timing_days": 0,
                "reasoning": f"Navio em nível NORMAM {current_level}. Limpeza imediata recomendada."
            })
        
        # Verificar exposição tropical
        level_3_milestone = next(
            (m for m in base_scenario.milestones if m.event == "reaches_level_3"),
            None
        )
        
        if level_3_milestone and level_3_milestone.day <= 60:
            # Verificar se rotas temperadas ajudariam
            temperate_scenario = next(
                (s for s in scenarios if s.name == "temperate_route"),
                None
            )
            
            if temperate_scenario:
                temperate_day = next(
                    (m.day for m in temperate_scenario.milestones 
                     if m.event == "reaches_level_3"),
                    None
                )
                
                if temperate_day and temperate_day > level_3_milestone.day + 15:
                    recommendations.append({
                        "action": "consider_route_optimization",
                        "urgency": "medium",
                        "optimal_timing_days": None,
                        "reasoning": f"Rotas temperadas podem adiar nível 3 em {temperate_day - level_3_milestone.day} dias"
                    })
        
        return recommendations
