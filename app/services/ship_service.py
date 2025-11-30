"""
Serviço de Navios.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from app.config import settings
from app.repositories.ship_repository import ShipRepository
from app.repositories.ais_repository import AISRepository
from app.repositories.biofouling_repository import BiofoulingRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.inspection_repository import InspectionRepository
from app.services.cache_service import CacheService
from app.schemas.ship import ShipFilterParams

logger = structlog.get_logger()


class ShipService:
    """
    Serviço para operações de navios.
    
    Combina dados de múltiplos repositórios e aplica lógica de negócio.
    """
    
    def __init__(
        self,
        ship_repo: ShipRepository,
        ais_repo: AISRepository,
        biofouling_repo: BiofoulingRepository,
        alert_repo: AlertRepository,
        inspection_repo: InspectionRepository,
        cache_service: CacheService
    ):
        """Inicializa o serviço."""
        self.ship_repo = ship_repo
        self.ais_repo = ais_repo
        self.biofouling_repo = biofouling_repo
        self.alert_repo = alert_repo
        self.inspection_repo = inspection_repo
        self.cache = cache_service
    
    async def list_ships(
        self,
        params: ShipFilterParams
    ) -> Dict[str, Any]:
        """
        Lista navios com filtros e status de bioincrustação.
        
        Args:
            params: Parâmetros de filtro
            
        Returns:
            Dicionário com total e lista de navios
        """
        # Criar hash dos filtros para cache
        filters_hash = hashlib.md5(
            f"{params.status}:{params.ship_class}:{params.sort_by}:{params.order}:{params.limit}:{params.offset}".encode()
        ).hexdigest()[:16]
        
        # Verificar cache
        cached = await self.cache.get_ships_list(filters_hash)
        if cached:
            logger.debug("ships_list_cache_hit", filters_hash=filters_hash)
            return cached
        
        logger.info("listing_ships", params=params.model_dump())
        
        # Buscar navios
        ships = await self.ship_repo.list_with_filters(
            ship_class=params.ship_class,
            sort_by=params.sort_by,
            order=params.order,
            skip=params.offset,
            limit=params.limit
        )
        
        # Buscar índices mais recentes
        latest_indices = await self.biofouling_repo.get_all_latest()
        index_map = {idx.ship_id: idx for idx in latest_indices}
        
        # Construir resposta
        ships_data = []
        for ship in ships:
            ship_data = await self._build_ship_response(ship, index_map.get(ship.id))
            
            # Filtrar por status se especificado
            if params.status:
                if ship_data.get("status") != params.status:
                    continue
            
            ships_data.append(ship_data)
        
        # Total (sem filtro de status para paginação correta)
        total = await self.ship_repo.count(ship_class=params.ship_class)
        
        result = {
            "total": total,
            "ships": ships_data
        }
        
        # Cachear resultado
        await self.cache.set_ships_list(filters_hash, result)
        
        return result
    
    async def get_ship_detail(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca detalhes completos de um navio.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Detalhes do navio ou None
        """
        # Verificar cache
        cached = await self.cache.get_ship_detail(ship_id)
        if cached:
            logger.debug("ship_detail_cache_hit", ship_id=ship_id)
            return cached
        
        logger.info("getting_ship_detail", ship_id=ship_id)
        
        # Buscar navio
        ship = await self.ship_repo.get_with_relations(ship_id)
        if not ship:
            return None
        
        # Buscar dados relacionados
        latest_index = await self.biofouling_repo.get_latest(ship_id)
        latest_position = await self.ais_repo.get_latest_position(ship_id)
        recent_indices = await self.biofouling_repo.get_history(ship_id, limit=30)
        active_alerts = await self.alert_repo.get_ship_alerts(ship_id)
        latest_inspection = await self.inspection_repo.get_latest(ship_id)
        
        # Construir resposta detalhada
        result = {
            "id": ship.id,
            "name": ship.name,
            "class": ship.ship_class,
            "specifications": {
                "length_m": ship.length_m,
                "beam_m": ship.beam_m,
                "draft_m": ship.draft_m,
                "gross_tonnage": ship.gross_tonnage
            },
            "current_status": None,
            "current_position": None,
            "recent_events": [],
            "historical_indices": [],
            "alerts": []
        }
        
        # Status atual
        if latest_index:
            result["current_status"] = {
                "index": latest_index.index_value,
                "normam_level": latest_index.normam_level,
                "status": latest_index.status,
                "components": latest_index.components,
                "calculated_at": latest_index.calculated_at.isoformat()
            }
        
        # Posição atual
        if latest_position:
            result["current_position"] = {
                "latitude": latest_position.latitude,
                "longitude": latest_position.longitude,
                "timestamp": latest_position.timestamp.isoformat(),
                "speed": latest_position.speed,
                "heading": latest_position.heading
            }
        
        # Histórico de índices
        for idx in recent_indices[:30]:
            result["historical_indices"].append({
                "date": idx.calculated_at.date().isoformat(),
                "index": idx.index_value
            })
        
        # Alertas ativos
        for alert in active_alerts[:10]:
            result["alerts"].append({
                "id": alert.id,
                "type": alert.severity,
                "message": alert.message,
                "created_at": alert.created_at.isoformat()
            })
        
        # Cachear resultado
        await self.cache.set_ship_detail(ship_id, result)
        
        return result
    
    async def get_ship_timeline(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day"
    ) -> Optional[Dict[str, Any]]:
        """
        Busca timeline detalhado do navio.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            interval: Intervalo de agregação
            
        Returns:
            Timeline ou None
        """
        # Verificar cache
        params_hash = hashlib.md5(
            f"{start_date}:{end_date}:{interval}".encode()
        ).hexdigest()[:16]
        
        cached = await self.cache.get_ship_timeline(ship_id, params_hash)
        if cached:
            return cached
        
        logger.info(
            "getting_ship_timeline",
            ship_id=ship_id,
            start=start_date,
            end=end_date
        )
        
        # Buscar navio
        ship = await self.ship_repo.get_by_id(ship_id)
        if not ship:
            return None
        
        # Buscar histórico de índices
        indices = await self.biofouling_repo.get_history(
            ship_id,
            start_date=start_date,
            end_date=end_date,
            limit=500
        )
        
        # Buscar inspeções no período
        inspections = await self.inspection_repo.get_inspections_in_range(
            start_date.date(),
            end_date.date(),
            ship_id=ship_id
        )
        
        # Construir pontos de dados
        data_points = []
        for idx in indices:
            data_points.append({
                "timestamp": idx.calculated_at.isoformat(),
                "index": idx.index_value,
                "normam_level": idx.normam_level,
                "components": idx.components,
                "position": None,  # TODO: enriquecer com posição
                "environmental_exposure": None  # TODO: calcular
            })
        
        # Calcular estatísticas
        if indices:
            index_values = [i.index_value for i in indices]
            stats = {
                "avg_index": sum(index_values) / len(index_values),
                "max_index": max(index_values),
                "min_index": min(index_values),
                "degradation_rate_per_month": await self.biofouling_repo.calculate_degradation_rate(ship_id)
            }
        else:
            stats = {
                "avg_index": 0,
                "max_index": 0,
                "min_index": 0,
                "degradation_rate_per_month": 0
            }
        
        # Eventos (limpezas, inspeções)
        events = []
        for insp in inspections:
            events.append({
                "type": "inspection",
                "date": insp.inspection_date.isoformat(),
                "location": insp.location,
                "normam_level_confirmed": insp.normam_level_confirmed
            })
        
        result = {
            "ship_id": ship_id,
            "ship_name": ship.name,
            "period": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat()
            },
            "data_points": data_points,
            "statistics": stats,
            "events": events
        }
        
        # Cachear
        await self.cache.set_ship_timeline(ship_id, params_hash, result)
        
        return result
    
    async def _build_ship_response(
        self,
        ship,
        latest_index
    ) -> Dict[str, Any]:
        """
        Constrói resposta de navio para lista.
        
        Args:
            ship: Modelo do navio
            latest_index: Índice mais recente
            
        Returns:
            Dicionário com dados do navio
        """
        # Buscar última posição
        latest_position = await self.ais_repo.get_latest_position(ship.id)
        
        # Buscar última inspeção
        latest_inspection = await self.inspection_repo.get_latest(ship.id)
        
        result = {
            "id": ship.id,
            "name": ship.name,
            "class": ship.ship_class,
            "current_index": None,
            "normam_level": None,
            "status": None,
            "last_position": None,
            "last_inspection_date": None,
            "days_since_cleaning": ship.days_since_cleaning,
            "components": None
        }
        
        if latest_index:
            result.update({
                "current_index": latest_index.index_value,
                "normam_level": latest_index.normam_level,
                "status": latest_index.status,
                "components": latest_index.components
            })
        
        if latest_position:
            result["last_position"] = {
                "latitude": latest_position.latitude,
                "longitude": latest_position.longitude,
                "timestamp": latest_position.timestamp.isoformat(),
                "speed": latest_position.speed
            }
        
        if latest_inspection:
            result["last_inspection_date"] = latest_inspection.inspection_date.isoformat()
        
        return result
    
    async def create_ship(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria novo navio.
        
        Args:
            data: Dados do navio
            
        Returns:
            Navio criado
        """
        logger.info("creating_ship", name=data.get("name"))
        
        ship = await self.ship_repo.create(data)
        
        # Invalidar caches
        await self.cache.delete_pattern("ships:*")
        
        return ship.to_dict()
    
    async def update_ship(
        self,
        ship_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza navio existente.
        
        Args:
            ship_id: UUID do navio
            data: Dados para atualização
            
        Returns:
            Navio atualizado ou None
        """
        logger.info("updating_ship", ship_id=ship_id)
        
        ship = await self.ship_repo.update(ship_id, data)
        if not ship:
            return None
        
        # Invalidar caches
        await self.cache.invalidate_ship(ship_id)
        
        return ship.to_dict()
