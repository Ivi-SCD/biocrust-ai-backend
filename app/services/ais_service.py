"""
Serviço de dados AIS.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import structlog

from app.repositories.ais_repository import AISRepository
from app.repositories.ship_repository import ShipRepository
from app.services.cache_service import CacheService

logger = structlog.get_logger()


class AISService:
    """
    Serviço para processamento de dados AIS.
    """
    
    def __init__(
        self,
        ais_repo: AISRepository,
        ship_repo: ShipRepository,
        cache_service: CacheService
    ):
        """Inicializa o serviço."""
        self.ais_repo = ais_repo
        self.ship_repo = ship_repo
        self.cache = cache_service
    
    async def ingest_positions(
        self,
        positions: List[Dict[str, Any]]
    ) -> Tuple[int, int, str]:
        """
        Ingere posições AIS em batch.
        
        Args:
            positions: Lista de posições
            
        Returns:
            Tupla (aceitas, rejeitadas, processing_id)
        """
        processing_id = str(uuid4())
        
        logger.info(
            "ingesting_ais_positions",
            count=len(positions),
            processing_id=processing_id
        )
        
        accepted = 0
        rejected = 0
        valid_positions = []
        
        for pos in positions:
            try:
                # Validar e resolver ship_id
                ship_name = pos.get("ship_name")
                ship = await self.ship_repo.get_by_name(ship_name)
                
                if not ship:
                    logger.warning(
                        "ship_not_found_for_ais",
                        ship_name=ship_name
                    )
                    rejected += 1
                    continue
                
                # Preparar dados
                valid_positions.append({
                    "ship_id": ship.id,
                    "timestamp": pos.get("timestamp"),
                    "latitude": pos.get("latitude"),
                    "longitude": pos.get("longitude"),
                    "speed": pos.get("speed"),
                    "heading": pos.get("heading")
                })
                accepted += 1
                
            except Exception as e:
                logger.error(
                    "ais_position_validation_error",
                    error=str(e)
                )
                rejected += 1
        
        # Inserir em batch
        if valid_positions:
            await self.ais_repo.bulk_insert(valid_positions)
            
            # Invalidar caches relacionados
            ship_ids = set(p["ship_id"] for p in valid_positions)
            for ship_id in ship_ids:
                await self.cache.invalidate_ship(ship_id)
        
        logger.info(
            "ais_ingestion_complete",
            accepted=accepted,
            rejected=rejected,
            processing_id=processing_id
        )
        
        return accepted, rejected, processing_id
    
    async def get_track(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime,
        simplify: bool = True,
        max_points: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        Busca trajetória do navio.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            simplify: Simplificar trajetória
            max_points: Máximo de pontos
            
        Returns:
            Trajetória ou None
        """
        # Verificar cache
        params_hash = hashlib.md5(
            f"{start_date}:{end_date}:{simplify}:{max_points}".encode()
        ).hexdigest()[:16]
        
        cached = await self.cache.get_track(ship_id, params_hash)
        if cached:
            return cached
        
        logger.info(
            "getting_ship_track",
            ship_id=ship_id,
            start=start_date,
            end=end_date
        )
        
        # Buscar navio
        ship = await self.ship_repo.get_by_id(ship_id)
        if not ship:
            return None
        
        # Contar total de pontos
        total_points = await self.ais_repo.count_positions_in_range(
            ship_id, start_date, end_date
        )
        
        # Buscar posições
        if simplify and total_points > max_points:
            positions = await self.ais_repo.get_positions_simplified(
                ship_id, start_date, end_date, max_points
            )
        else:
            positions = await self.ais_repo.get_positions_in_range(
                ship_id, start_date, end_date, limit=max_points
            )
        
        # Calcular estatísticas
        stats = await self._calculate_track_statistics(
            ship_id, start_date, end_date, positions
        )
        
        # Formatar trajetória
        track = [
            {
                "timestamp": pos.timestamp.isoformat(),
                "lat": pos.latitude,
                "lon": pos.longitude,
                "speed": pos.speed,
                "heading": pos.heading
            }
            for pos in positions
        ]
        
        result = {
            "ship_id": ship_id,
            "ship_name": ship.name,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_points": total_points,
            "simplified_points": len(positions),
            "track": track,
            "statistics": stats,
            "ports_visited": []  # TODO: detectar portos
        }
        
        # Cachear
        await self.cache.set_track(ship_id, params_hash, result)
        
        return result
    
    async def _calculate_track_statistics(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime,
        positions: List
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas da trajetória.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            positions: Lista de posições
            
        Returns:
            Dicionário com estatísticas
        """
        # Calcular distância total
        total_distance = await self.ais_repo.calculate_distance(
            ship_id, start_date, end_date
        )
        
        # Calcular horas por tipo de água
        tropical, subtropical, temperate = await self.ais_repo.calculate_water_type_hours(
            ship_id, start_date, end_date
        )
        
        # Calcular velocidades
        speeds = [p.speed for p in positions if p.speed is not None]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        
        return {
            "total_distance_nm": round(total_distance, 1),
            "avg_speed": round(avg_speed, 1),
            "max_speed": round(max_speed, 1),
            "time_in_tropical_waters_hours": round(tropical, 1),
            "time_in_subtropical_waters_hours": round(subtropical, 1),
            "time_in_temperate_waters_hours": round(temperate, 1)
        }
    
    async def update_environmental_metrics(
        self,
        ship_id: str,
        days: int = 30
    ) -> Dict[str, float]:
        """
        Atualiza métricas ambientais do navio.
        
        Args:
            ship_id: UUID do navio
            days: Período para análise
            
        Returns:
            Métricas calculadas
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        tropical, subtropical, temperate = await self.ais_repo.calculate_water_type_hours(
            ship_id, start_date, end_date
        )
        
        # Atualizar no banco
        await self.ship_repo.update_environmental_metrics(
            ship_id=ship_id,
            period_start=start_date.date(),
            period_end=end_date.date(),
            tropical_hours=tropical,
            subtropical_hours=subtropical,
            temperate_hours=temperate
        )
        
        return {
            "tropical_hours": tropical,
            "subtropical_hours": subtropical,
            "temperate_hours": temperate
        }
