"""
Repositório de Navios.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ship import Ship, ShipEnvironmentalMetrics
from app.repositories.base import BaseRepository


class ShipRepository(BaseRepository[Ship]):
    """
    Repositório para operações de navios.
    """
    
    def __init__(self, db: AsyncSession):
        """Inicializa o repositório."""
        super().__init__(Ship, db)
    
    async def get_by_name(self, name: str) -> Optional[Ship]:
        """
        Busca navio por nome.
        
        Args:
            name: Nome do navio
            
        Returns:
            Navio encontrado ou None
        """
        query = select(Ship).where(Ship.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_relations(self, ship_id: str) -> Optional[Ship]:
        """
        Busca navio com relações carregadas.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Navio com relações ou None
        """
        query = (
            select(Ship)
            .where(Ship.id == ship_id)
            .options(
                selectinload(Ship.environmental_metrics)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_with_filters(
        self,
        ship_class: Optional[str] = None,
        sort_by: str = "name",
        order: str = "asc",
        skip: int = 0,
        limit: int = 50
    ) -> List[Ship]:
        """
        Lista navios com filtros e ordenação.
        
        Args:
            ship_class: Filtrar por classe
            sort_by: Campo para ordenação
            order: asc ou desc
            skip: Offset
            limit: Limite
            
        Returns:
            Lista de navios
        """
        query = select(Ship)
        
        if ship_class:
            query = query.where(Ship.ship_class == ship_class)
        
        # Ordenação
        sort_column = getattr(Ship, sort_by, Ship.name)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_names(self) -> List[str]:
        """
        Retorna lista de nomes de todos os navios.
        
        Returns:
            Lista de nomes
        """
        query = select(Ship.name).order_by(Ship.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_class(self, ship_class: str) -> List[Ship]:
        """
        Busca navios por classe.
        
        Args:
            ship_class: Classe do navio
            
        Returns:
            Lista de navios da classe
        """
        query = select(Ship).where(Ship.ship_class == ship_class)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_classes(self) -> List[str]:
        """
        Retorna lista de classes únicas.
        
        Returns:
            Lista de classes
        """
        query = select(Ship.ship_class).distinct().order_by(Ship.ship_class)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_cleaning_date(
        self,
        ship_id: str,
        cleaning_date: date
    ) -> Optional[Ship]:
        """
        Atualiza data de última limpeza.
        
        Args:
            ship_id: UUID do navio
            cleaning_date: Nova data de limpeza
            
        Returns:
            Navio atualizado ou None
        """
        return await self.update(ship_id, {"last_cleaning_date": cleaning_date})
    
    async def update_environmental_metrics(
        self,
        ship_id: str,
        period_start: date,
        period_end: date,
        tropical_hours: float,
        subtropical_hours: float,
        temperate_hours: float
    ) -> ShipEnvironmentalMetrics:
        """
        Atualiza ou cria métricas ambientais do navio.
        
        Args:
            ship_id: UUID do navio
            period_start: Início do período
            period_end: Fim do período
            tropical_hours: Horas em águas tropicais
            subtropical_hours: Horas em águas subtropicais
            temperate_hours: Horas em águas temperadas
            
        Returns:
            Métricas atualizadas
        """
        query = select(ShipEnvironmentalMetrics).where(
            ShipEnvironmentalMetrics.ship_id == ship_id
        )
        result = await self.db.execute(query)
        metrics = result.scalar_one_or_none()
        
        if metrics:
            metrics.period_start = period_start
            metrics.period_end = period_end
            metrics.tropical_hours = tropical_hours
            metrics.subtropical_hours = subtropical_hours
            metrics.temperate_hours = temperate_hours
        else:
            metrics = ShipEnvironmentalMetrics(
                ship_id=ship_id,
                period_start=period_start,
                period_end=period_end,
                tropical_hours=tropical_hours,
                subtropical_hours=subtropical_hours,
                temperate_hours=temperate_hours
            )
            self.db.add(metrics)
        
        await self.db.commit()
        await self.db.refresh(metrics)
        return metrics
    
    async def get_environmental_metrics(
        self,
        ship_id: str
    ) -> Optional[ShipEnvironmentalMetrics]:
        """
        Busca métricas ambientais do navio.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Métricas ou None
        """
        query = select(ShipEnvironmentalMetrics).where(
            ShipEnvironmentalMetrics.ship_id == ship_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
