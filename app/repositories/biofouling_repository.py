"""
Repositório de Índices de Bioincrustação.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.biofouling_index import BiofoulingIndex
from app.repositories.base import BaseRepository


class BiofoulingRepository(BaseRepository[BiofoulingIndex]):
    """
    Repositório para operações de índices de bioincrustação.
    """
    
    def __init__(self, db: AsyncSession):
        """Inicializa o repositório."""
        super().__init__(BiofoulingIndex, db)
    
    async def get_latest(self, ship_id: str) -> Optional[BiofoulingIndex]:
        """
        Busca índice mais recente do navio.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Índice mais recente ou None
        """
        query = (
            select(BiofoulingIndex)
            .where(BiofoulingIndex.ship_id == ship_id)
            .order_by(BiofoulingIndex.calculated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_history(
        self,
        ship_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[BiofoulingIndex]:
        """
        Busca histórico de índices.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            limit: Limite de resultados
            
        Returns:
            Lista de índices
        """
        query = (
            select(BiofoulingIndex)
            .where(BiofoulingIndex.ship_id == ship_id)
        )
        
        if start_date:
            query = query.where(BiofoulingIndex.calculated_at >= start_date)
        if end_date:
            query = query.where(BiofoulingIndex.calculated_at <= end_date)
        
        query = query.order_by(BiofoulingIndex.calculated_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_latest(self) -> List[BiofoulingIndex]:
        """
        Busca índice mais recente de cada navio.
        
        Returns:
            Lista de índices mais recentes
        """
        # Subquery para obter o timestamp mais recente de cada navio
        subquery = (
            select(
                BiofoulingIndex.ship_id,
                func.max(BiofoulingIndex.calculated_at).label("max_calc")
            )
            .group_by(BiofoulingIndex.ship_id)
            .subquery()
        )
        
        # Query principal
        query = (
            select(BiofoulingIndex)
            .join(
                subquery,
                and_(
                    BiofoulingIndex.ship_id == subquery.c.ship_id,
                    BiofoulingIndex.calculated_at == subquery.c.max_calc
                )
            )
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_fleet_summary_stats(self) -> Dict[str, Any]:
        """
        Calcula estatísticas resumidas da frota.
        
        Returns:
            Dicionário com estatísticas
        """
        # Buscar índices mais recentes
        latest_indices = await self.get_all_latest()
        
        if not latest_indices:
            return {
                "total": 0,
                "avg_index": 0,
                "status_distribution": {"ok": 0, "warning": 0, "critical": 0},
                "level_distribution": {f"level_{i}": 0 for i in range(5)}
            }
        
        # Calcular distribuições
        status_dist = {"ok": 0, "warning": 0, "critical": 0}
        level_dist = {f"level_{i}": 0 for i in range(5)}
        total_index = 0
        
        for idx in latest_indices:
            total_index += idx.index_value
            
            # Status
            if idx.normam_level <= 1:
                status_dist["ok"] += 1
            elif idx.normam_level == 2:
                status_dist["warning"] += 1
            else:
                status_dist["critical"] += 1
            
            # Level
            level_key = f"level_{min(idx.normam_level, 4)}"
            level_dist[level_key] += 1
        
        return {
            "total": len(latest_indices),
            "avg_index": total_index / len(latest_indices),
            "status_distribution": status_dist,
            "level_distribution": level_dist
        }
    
    async def get_worst_ships(self, limit: int = 5) -> List[BiofoulingIndex]:
        """
        Busca navios com piores índices.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de índices
        """
        latest = await self.get_all_latest()
        sorted_indices = sorted(latest, key=lambda x: x.index_value, reverse=True)
        return sorted_indices[:limit]
    
    async def get_best_ships(self, limit: int = 5) -> List[BiofoulingIndex]:
        """
        Busca navios com melhores índices.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de índices
        """
        latest = await self.get_all_latest()
        sorted_indices = sorted(latest, key=lambda x: x.index_value)
        return sorted_indices[:limit]
    
    async def get_average_by_class(self, ship_class: str) -> float:
        """
        Calcula média de índice por classe.
        
        Args:
            ship_class: Classe do navio
            
        Returns:
            Média do índice
        """
        from app.models.ship import Ship
        
        # Subquery para índices mais recentes
        subquery = (
            select(
                BiofoulingIndex.ship_id,
                func.max(BiofoulingIndex.calculated_at).label("max_calc")
            )
            .group_by(BiofoulingIndex.ship_id)
            .subquery()
        )
        
        # Query com join na tabela de ships
        query = (
            select(func.avg(BiofoulingIndex.index_value))
            .join(
                subquery,
                and_(
                    BiofoulingIndex.ship_id == subquery.c.ship_id,
                    BiofoulingIndex.calculated_at == subquery.c.max_calc
                )
            )
            .join(Ship, Ship.id == BiofoulingIndex.ship_id)
            .where(Ship.ship_class == ship_class)
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0.0
    
    async def calculate_degradation_rate(
        self,
        ship_id: str,
        days: int = 30
    ) -> float:
        """
        Calcula taxa de degradação mensal.
        
        Args:
            ship_id: UUID do navio
            days: Período para análise
            
        Returns:
            Taxa de degradação por mês
        """
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        history = await self.get_history(ship_id, start_date, end_date)
        
        if len(history) < 2:
            return 0.0
        
        # Ordenar por data
        history = sorted(history, key=lambda x: x.calculated_at)
        
        # Calcular taxa de mudança
        first = history[0]
        last = history[-1]
        
        days_elapsed = (last.calculated_at - first.calculated_at).days
        if days_elapsed == 0:
            return 0.0
        
        change = last.index_value - first.index_value
        monthly_rate = (change / days_elapsed) * 30
        
        return monthly_rate
    
    async def bulk_insert(
        self,
        indices: List[Dict[str, Any]]
    ) -> int:
        """
        Insere múltiplos índices em batch.
        
        Args:
            indices: Lista de dicionários com dados
            
        Returns:
            Número de índices inseridos
        """
        from uuid import uuid4
        
        for idx in indices:
            if "id" not in idx:
                idx["id"] = str(uuid4())
            if "created_at" not in idx:
                idx["created_at"] = datetime.utcnow()
        
        await self.db.execute(
            BiofoulingIndex.__table__.insert(),
            indices
        )
        await self.db.commit()
        
        return len(indices)
