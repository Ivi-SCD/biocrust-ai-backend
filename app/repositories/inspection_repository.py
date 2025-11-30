"""
Repositório de Inspeções.
"""

from datetime import date
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inspection import Inspection
from app.repositories.base import BaseRepository


class InspectionRepository(BaseRepository[Inspection]):
    """
    Repositório para operações de inspeções.
    """
    
    def __init__(self, db: AsyncSession):
        """Inicializa o repositório."""
        super().__init__(Inspection, db)
    
    async def get_latest(self, ship_id: str) -> Optional[Inspection]:
        """
        Busca inspeção mais recente do navio.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Inspeção mais recente ou None
        """
        query = (
            select(Inspection)
            .where(Inspection.ship_id == ship_id)
            .order_by(Inspection.inspection_date.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_ship_inspections(
        self,
        ship_id: str,
        limit: int = 10
    ) -> List[Inspection]:
        """
        Busca inspeções de um navio.
        
        Args:
            ship_id: UUID do navio
            limit: Limite de resultados
            
        Returns:
            Lista de inspeções
        """
        query = (
            select(Inspection)
            .where(Inspection.ship_id == ship_id)
            .order_by(Inspection.inspection_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_inspections_in_range(
        self,
        start_date: date,
        end_date: date,
        ship_id: Optional[str] = None
    ) -> List[Inspection]:
        """
        Busca inspeções em um período.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            ship_id: Filtrar por navio (opcional)
            
        Returns:
            Lista de inspeções
        """
        query = (
            select(Inspection)
            .where(
                and_(
                    Inspection.inspection_date >= start_date,
                    Inspection.inspection_date <= end_date
                )
            )
        )
        
        if ship_id:
            query = query.where(Inspection.ship_id == ship_id)
        
        query = query.order_by(Inspection.inspection_date.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_last_cleaning_date(self, ship_id: str) -> Optional[date]:
        """
        Busca data da última limpeza (registrada como inspeção de limpeza).
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Data da última limpeza ou None
        """
        # Buscar inspeção que indica limpeza (normam_level = 0)
        query = (
            select(Inspection.inspection_date)
            .where(
                and_(
                    Inspection.ship_id == ship_id,
                    Inspection.normam_level_confirmed == 0
                )
            )
            .order_by(Inspection.inspection_date.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def count_by_normam_level(
        self,
        normam_level: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        Conta inspeções por nível NORMAM.
        
        Args:
            normam_level: Nível NORMAM
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Número de inspeções
        """
        query = select(func.count(Inspection.id)).where(
            Inspection.normam_level_confirmed == normam_level
        )
        
        if start_date:
            query = query.where(Inspection.inspection_date >= start_date)
        if end_date:
            query = query.where(Inspection.inspection_date <= end_date)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
