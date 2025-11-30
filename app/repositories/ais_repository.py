"""
Repositório de Posições AIS.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ais_position import AISPosition
from app.repositories.base import BaseRepository


class AISRepository(BaseRepository[AISPosition]):
    """
    Repositório para operações de dados AIS.
    """
    
    def __init__(self, db: AsyncSession):
        """Inicializa o repositório."""
        super().__init__(AISPosition, db)
    
    async def get_latest_position(self, ship_id: str) -> Optional[AISPosition]:
        """
        Busca posição mais recente do navio.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Posição mais recente ou None
        """
        query = (
            select(AISPosition)
            .where(AISPosition.ship_id == ship_id)
            .order_by(AISPosition.timestamp.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_positions_in_range(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None
    ) -> List[AISPosition]:
        """
        Busca posições em um intervalo de datas.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            limit: Limite de resultados
            
        Returns:
            Lista de posições
        """
        query = (
            select(AISPosition)
            .where(
                and_(
                    AISPosition.ship_id == ship_id,
                    AISPosition.timestamp >= start_date,
                    AISPosition.timestamp <= end_date
                )
            )
            .order_by(AISPosition.timestamp.asc())
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_positions_in_range(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        Conta posições em um intervalo.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Número de posições
        """
        query = (
            select(func.count(AISPosition.id))
            .where(
                and_(
                    AISPosition.ship_id == ship_id,
                    AISPosition.timestamp >= start_date,
                    AISPosition.timestamp <= end_date
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def bulk_insert(self, positions: List[Dict[str, Any]]) -> int:
        """
        Insere múltiplas posições em batch.
        
        Args:
            positions: Lista de dicionários com dados das posições
            
        Returns:
            Número de posições inseridas
        """
        if not positions:
            return 0
        
        from uuid import uuid4
        
        for pos in positions:
            if "id" not in pos:
                pos["id"] = str(uuid4())
            if "created_at" not in pos:
                pos["created_at"] = datetime.utcnow()
        
        await self.db.execute(
            AISPosition.__table__.insert(),
            positions
        )
        await self.db.commit()
        
        return len(positions)
    
    async def get_positions_simplified(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime,
        max_points: int = 500
    ) -> List[AISPosition]:
        """
        Busca posições simplificadas (amostragem para reduzir pontos).
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            max_points: Máximo de pontos
            
        Returns:
            Lista de posições simplificadas
        """
        # Primeiro, contar total de pontos
        total = await self.count_positions_in_range(ship_id, start_date, end_date)
        
        if total <= max_points:
            return await self.get_positions_in_range(ship_id, start_date, end_date)
        
        # Calcular intervalo de amostragem
        sample_interval = total // max_points
        
        # Query com amostragem usando ROW_NUMBER
        query = text("""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (ORDER BY timestamp) as rn
                FROM ais_positions
                WHERE ship_id = :ship_id
                AND timestamp >= :start_date
                AND timestamp <= :end_date
            ) t
            WHERE rn % :interval = 0
            ORDER BY timestamp
            LIMIT :max_points
        """)
        
        result = await self.db.execute(
            query,
            {
                "ship_id": ship_id,
                "start_date": start_date,
                "end_date": end_date,
                "interval": sample_interval,
                "max_points": max_points
            }
        )
        
        rows = result.fetchall()
        
        # Converter para objetos AISPosition
        positions = []
        for row in rows:
            pos = AISPosition(
                id=row.id,
                ship_id=row.ship_id,
                timestamp=row.timestamp,
                latitude=row.latitude,
                longitude=row.longitude,
                speed=row.speed,
                heading=row.heading,
                created_at=row.created_at
            )
            positions.append(pos)
        
        return positions
    
    async def calculate_distance(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calcula distância total percorrida no período.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Distância em milhas náuticas
        """
        # Buscar posições
        positions = await self.get_positions_in_range(ship_id, start_date, end_date)
        
        if len(positions) < 2:
            return 0.0
        
        # Calcular distância usando fórmula de Haversine
        import math
        
        total_distance = 0.0
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]
            
            # Haversine formula
            lat1, lon1 = math.radians(prev.latitude), math.radians(prev.longitude)
            lat2, lon2 = math.radians(curr.latitude), math.radians(curr.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            # Raio da Terra em milhas náuticas
            r = 3440.065
            
            total_distance += c * r
        
        return total_distance
    
    async def calculate_water_type_hours(
        self,
        ship_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[float, float, float]:
        """
        Calcula horas em cada tipo de água.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Tupla (tropical_hours, subtropical_hours, temperate_hours)
        """
        positions = await self.get_positions_in_range(ship_id, start_date, end_date)
        
        tropical_hours = 0.0
        subtropical_hours = 0.0
        temperate_hours = 0.0
        
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]
            
            # Calcular duração entre posições
            duration_hours = (curr.timestamp - prev.timestamp).total_seconds() / 3600
            
            # Classificar tipo de água baseado na latitude média
            avg_lat = (prev.latitude + curr.latitude) / 2
            abs_lat = abs(avg_lat)
            
            if abs_lat < 20:
                tropical_hours += duration_hours
            elif abs_lat < 35:
                subtropical_hours += duration_hours
            else:
                temperate_hours += duration_hours
        
        return tropical_hours, subtropical_hours, temperate_hours
