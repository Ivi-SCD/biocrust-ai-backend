"""
Repositório de Eventos de Navegação.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.navigation_event import NavigationEvent
from app.models.fuel_consumption import FuelConsumption
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[NavigationEvent]):
    """
    Repositório para operações de eventos de navegação.
    """
    
    def __init__(self, db: AsyncSession):
        """Inicializa o repositório."""
        super().__init__(NavigationEvent, db)
    
    async def get_by_session_id(self, session_id: int) -> Optional[NavigationEvent]:
        """
        Busca evento por session_id.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Evento encontrado ou None
        """
        query = (
            select(NavigationEvent)
            .where(NavigationEvent.session_id == session_id)
            .options(selectinload(NavigationEvent.fuel_consumption))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_ship_events(
        self,
        ship_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[NavigationEvent]:
        """
        Busca eventos de um navio.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista de eventos
        """
        query = (
            select(NavigationEvent)
            .where(NavigationEvent.ship_id == ship_id)
            .options(selectinload(NavigationEvent.fuel_consumption))
        )
        
        if start_date:
            query = query.where(NavigationEvent.start_date >= start_date)
        if end_date:
            query = query.where(NavigationEvent.start_date <= end_date)
        
        query = query.order_by(NavigationEvent.start_date.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_events(
        self,
        ship_id: str,
        days: int = 30
    ) -> List[NavigationEvent]:
        """
        Busca eventos recentes de um navio.
        
        Args:
            ship_id: UUID do navio
            days: Número de dias para buscar
            
        Returns:
            Lista de eventos
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        return await self.get_ship_events(ship_id, start_date=start_date)
    
    async def get_events_for_calculation(
        self,
        ship_id: str,
        limit: int = 30
    ) -> List[NavigationEvent]:
        """
        Busca eventos para cálculo de bioincrustação.
        
        Args:
            ship_id: UUID do navio
            limit: Limite de eventos
            
        Returns:
            Lista de eventos com dados completos
        """
        query = (
            select(NavigationEvent)
            .where(
                and_(
                    NavigationEvent.ship_id == ship_id,
                    NavigationEvent.distance_nm.isnot(None),
                    NavigationEvent.avg_speed.isnot(None)
                )
            )
            .options(selectinload(NavigationEvent.fuel_consumption))
            .order_by(NavigationEvent.start_date.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def bulk_insert_with_fuel(
        self,
        events: List[Dict[str, Any]],
        fuel_data: List[Dict[str, Any]]
    ) -> int:
        """
        Insere eventos e consumo de combustível em batch.
        
        Args:
            events: Lista de dicionários com eventos
            fuel_data: Lista de dicionários com consumo
            
        Returns:
            Número de eventos inseridos
        """
        from uuid import uuid4
        
        # Inserir eventos
        for event in events:
            if "id" not in event:
                event["id"] = str(uuid4())
        
        await self.db.execute(
            NavigationEvent.__table__.insert(),
            events
        )
        
        # Inserir consumo de combustível
        if fuel_data:
            for fuel in fuel_data:
                if "id" not in fuel:
                    fuel["id"] = str(uuid4())
            
            await self.db.execute(
                FuelConsumption.__table__.insert(),
                fuel_data
            )
        
        await self.db.commit()
        
        return len(events)
    
    async def get_total_distance(
        self,
        ship_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Calcula distância total navegada.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Distância total em milhas náuticas
        """
        query = select(func.sum(NavigationEvent.distance_nm)).where(
            NavigationEvent.ship_id == ship_id
        )
        
        if start_date:
            query = query.where(NavigationEvent.start_date >= start_date)
        if end_date:
            query = query.where(NavigationEvent.start_date <= end_date)
        
        result = await self.db.execute(query)
        return result.scalar() or 0.0
    
    async def get_average_speed(
        self,
        ship_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Calcula velocidade média.
        
        Args:
            ship_id: UUID do navio
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Velocidade média em nós
        """
        query = select(func.avg(NavigationEvent.avg_speed)).where(
            and_(
                NavigationEvent.ship_id == ship_id,
                NavigationEvent.avg_speed.isnot(None)
            )
        )
        
        if start_date:
            query = query.where(NavigationEvent.start_date >= start_date)
        if end_date:
            query = query.where(NavigationEvent.start_date <= end_date)
        
        result = await self.db.execute(query)
        return result.scalar() or 0.0
