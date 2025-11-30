"""
Serviço de Bioincrustação.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from app.config import settings
from app.core.biofouling.calculator import BiofoulingCalculator
from app.core.biofouling.predictor import BiofoulingPredictor
from app.core.biofouling.roi_calculator import ROICalculator
from app.repositories.ship_repository import ShipRepository
from app.repositories.biofouling_repository import BiofoulingRepository
from app.repositories.event_repository import EventRepository
from app.services.cache_service import CacheService

logger = structlog.get_logger()


class BiofoulingService:
    """
    Serviço para cálculos de bioincrustação.
    
    Integra o modelo físico-estatístico e fornece cálculos de
    índice, previsões e ROI.
    """
    
    def __init__(
        self,
        ship_repo: ShipRepository,
        biofouling_repo: BiofoulingRepository,
        event_repo: EventRepository,
        cache_service: CacheService
    ):
        """Inicializa o serviço."""
        self.ship_repo = ship_repo
        self.biofouling_repo = biofouling_repo
        self.event_repo = event_repo
        self.cache = cache_service
        
        # Inicializar componentes de cálculo
        self.calculator = BiofoulingCalculator()
        self.predictor = BiofoulingPredictor()
        self.roi_calculator = ROICalculator()
    
    async def calculate_index(
        self,
        events: List[Dict[str, Any]],
        ship_length_m: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula índice de bioincrustação para eventos.
        
        Args:
            events: Lista de eventos de navegação
            ship_length_m: Comprimento do navio (opcional)
            
        Returns:
            Lista de resultados com índices calculados
        """
        logger.info(
            "calculating_biofouling_index",
            num_events=len(events),
            ship_length=ship_length_m
        )
        
        # Enriquecer eventos com dados do navio se necessário
        enriched_events = []
        for event in events:
            enriched = dict(event)
            
            # Buscar classe do navio se não fornecida
            if "ship_class" not in enriched:
                ship = await self.ship_repo.get_by_name(event.get("ship_name", ""))
                if ship:
                    enriched["ship_class"] = ship.ship_class
                    if not ship_length_m and ship.length_m:
                        ship_length_m = ship.length_m
            
            enriched_events.append(enriched)
        
        # Executar cálculo
        results = self.calculator.calculate_from_events(
            enriched_events,
            ship_length_m=ship_length_m
        )
        
        return results
    
    async def get_fleet_summary(self) -> Dict[str, Any]:
        """
        Gera resumo executivo da frota.
        
        Returns:
            Resumo com estatísticas da frota
        """
        # Verificar cache
        cached = await self.cache.get_fleet_summary()
        if cached:
            logger.debug("fleet_summary_cache_hit")
            return cached
        
        logger.info("generating_fleet_summary")
        
        # Buscar estatísticas
        stats = await self.biofouling_repo.get_fleet_summary_stats()
        
        # Buscar piores e melhores navios
        worst = await self.biofouling_repo.get_worst_ships(5)
        best = await self.biofouling_repo.get_best_ships(5)
        
        # Enriquecer com nomes dos navios
        worst_ships = []
        for idx in worst:
            ship = await self.ship_repo.get_by_id(idx.ship_id)
            if ship:
                worst_ships.append({
                    "name": ship.name,
                    "index": idx.index_value,
                    "level": idx.normam_level,
                    "days_since_cleaning": ship.days_since_cleaning
                })
        
        best_ships = []
        for idx in best:
            ship = await self.ship_repo.get_by_id(idx.ship_id)
            if ship:
                best_ships.append({
                    "name": ship.name,
                    "index": idx.index_value,
                    "level": idx.normam_level,
                    "days_since_cleaning": ship.days_since_cleaning
                })
        
        # Calcular impacto de custo
        critical_count = stats["status_distribution"]["critical"]
        additional_cost = critical_count * settings.CRITICAL_COST_PER_DAY * 30
        potential_savings = additional_cost * 0.7  # 70% recuperável com limpeza
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_ships": stats["total"],
            "status_distribution": stats["status_distribution"],
            "level_distribution": stats["level_distribution"],
            "average_index": round(stats["avg_index"], 1),
            "worst_ships": worst_ships,
            "best_ships": best_ships,
            "monthly_cost_impact": {
                "additional_fuel_cost_brl": round(additional_cost, 2),
                "potential_savings_brl": round(potential_savings, 2)
            }
        }
        
        # Cachear
        await self.cache.set_fleet_summary(result)
        
        return result
    
    async def generate_forecast(
        self,
        ship_id: str,
        forecast_days: int = 90,
        scenarios: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Gera previsão de degradação para um navio.
        
        Args:
            ship_id: UUID do navio
            forecast_days: Dias de previsão
            scenarios: Cenários a incluir
            
        Returns:
            Previsão ou None
        """
        logger.info(
            "generating_forecast",
            ship_id=ship_id,
            days=forecast_days
        )
        
        # Buscar navio e índice atual
        ship = await self.ship_repo.get_with_relations(ship_id)
        if not ship:
            return None
        
        latest_index = await self.biofouling_repo.get_latest(ship_id)
        if not latest_index:
            return None
        
        # Buscar métricas ambientais
        metrics = ship.environmental_metrics
        tropical_pct = 0.5  # Default
        if metrics and metrics.total_hours > 0:
            tropical_pct = metrics.tropical_percentage / 100
        
        # Gerar previsão
        prediction = self.predictor.predict(
            current_index=latest_index.index_value,
            forecast_days=forecast_days,
            tropical_exposure_pct=tropical_pct,
            include_scenarios=scenarios
        )
        
        # Formatar resposta
        result = {
            "ship_id": ship_id,
            "ship_name": ship.name,
            "current_index": latest_index.index_value,
            "forecast_period_days": forecast_days,
            "scenarios": [
                {
                    "scenario_name": s.name,
                    "description": s.description,
                    "predictions": [
                        {
                            "day": p.day,
                            "index": p.index,
                            "normam_level": p.normam_level,
                            "confidence_interval": {
                                "lower": p.confidence_lower,
                                "upper": p.confidence_upper
                            }
                        }
                        for p in s.predictions
                    ],
                    "milestones": [
                        {
                            "event": m.event,
                            "estimated_day": m.day,
                            "estimated_date": m.estimated_date.isoformat()
                        }
                        for m in s.milestones
                    ]
                }
                for s in prediction["scenarios"]
            ],
            "recommendations": prediction["recommendations"]
        }
        
        return result
    
    async def calculate_roi(
        self,
        ship_id: str,
        strategies: List[Dict[str, Any]],
        fuel_price_per_ton: Optional[float] = None,
        operational_days_per_year: int = 330,
        downtime_cost_per_day: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula ROI para estratégias de manutenção.
        
        Args:
            ship_id: UUID do navio
            strategies: Estratégias a analisar
            fuel_price_per_ton: Preço do combustível
            operational_days_per_year: Dias operacionais
            downtime_cost_per_day: Custo de parada
            
        Returns:
            Análise de ROI ou None
        """
        logger.info(
            "calculating_roi",
            ship_id=ship_id,
            num_strategies=len(strategies)
        )
        
        # Buscar navio e índice atual
        ship = await self.ship_repo.get_with_relations(ship_id)
        if not ship:
            return None
        
        latest_index = await self.biofouling_repo.get_latest(ship_id)
        if not latest_index:
            return None
        
        # Buscar exposição tropical
        metrics = ship.environmental_metrics
        tropical_pct = 0.5
        if metrics and metrics.total_hours > 0:
            tropical_pct = metrics.tropical_percentage / 100
        
        # Calcular ROI
        roi_result = self.roi_calculator.calculate_strategies(
            current_index=latest_index.index_value,
            strategies=strategies,
            fuel_price_per_ton=fuel_price_per_ton,
            operational_days_per_year=operational_days_per_year,
            downtime_cost_per_day=downtime_cost_per_day,
            tropical_exposure_pct=tropical_pct
        )
        
        # Formatar resposta
        result = {
            "ship_id": ship_id,
            "ship_name": ship.name,
            "current_index": latest_index.index_value,
            "analyzed_strategies": [
                {
                    "name": s.name,
                    "costs": {
                        "cleaning_cost": s.costs.cleaning_cost,
                        "downtime_cost": s.costs.downtime_cost,
                        "additional_fuel_cost": s.costs.additional_fuel_cost,
                        "total_cost": s.costs.total_cost
                    },
                    "savings": {
                        "fuel_saved_tons": s.savings.fuel_saved_tons,
                        "fuel_cost_saved": s.savings.fuel_cost_saved,
                        "net_savings": s.savings.net_savings
                    },
                    "roi_percentage": s.roi_percentage,
                    "payback_period_days": s.payback_period_days,
                    "npv_12_months": s.npv_12_months
                }
                for s in roi_result["analyzed_strategies"]
            ],
            "recommendation": roi_result["recommendation"]
        }
        
        return result
    
    async def save_calculated_index(
        self,
        ship_id: str,
        index_value: float,
        normam_level: int,
        components: Dict[str, float],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Salva índice calculado no banco de dados.
        
        Args:
            ship_id: UUID do navio
            index_value: Valor do índice
            normam_level: Nível NORMAM
            components: Componentes do índice
            metadata: Metadados adicionais
            
        Returns:
            UUID do registro criado
        """
        logger.info(
            "saving_biofouling_index",
            ship_id=ship_id,
            index=index_value,
            level=normam_level
        )
        
        data = {
            "ship_id": ship_id,
            "calculated_at": datetime.utcnow(),
            "index_value": index_value,
            "normam_level": normam_level,
            "component_efficiency": components.get("efficiency"),
            "component_environmental": components.get("environmental"),
            "component_temporal": components.get("temporal"),
            "component_operational": components.get("operational"),
            "metadata": metadata
        }
        
        record = await self.biofouling_repo.create(data)
        
        # Invalidar caches relacionados
        await self.cache.invalidate_ship(ship_id)
        await self.cache.delete_pattern("fleet:*")
        
        return record.id
