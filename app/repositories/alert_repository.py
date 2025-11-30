"""
Repositório de Alertas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """
    Repositório para operações de alertas.
    """
    
    def __init__(self, db: AsyncSession):
        """Inicializa o repositório."""
        super().__init__(Alert, db)
    
    async def get_with_ship(self, alert_id: str) -> Optional[Alert]:
        """
        Busca alerta com dados do navio.
        
        Args:
            alert_id: UUID do alerta
            
        Returns:
            Alerta com ship ou None
        """
        query = (
            select(Alert)
            .where(Alert.id == alert_id)
            .options(selectinload(Alert.ship))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_alerts(
        self,
        ship_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Alert]:
        """
        Lista alertas com filtros.
        
        Args:
            ship_id: Filtrar por navio
            severity: Filtrar por severidade
            status: Filtrar por status
            skip: Offset
            limit: Limite
            
        Returns:
            Lista de alertas
        """
        query = select(Alert).options(selectinload(Alert.ship))
        
        conditions = []
        if ship_id:
            conditions.append(Alert.ship_id == ship_id)
        if severity:
            conditions.append(Alert.severity == severity)
        if status:
            conditions.append(Alert.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_alerts(
        self,
        ship_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Conta alertas com filtros.
        
        Args:
            ship_id: Filtrar por navio
            severity: Filtrar por severidade
            status: Filtrar por status
            
        Returns:
            Número de alertas
        """
        query = select(func.count(Alert.id))
        
        conditions = []
        if ship_id:
            conditions.append(Alert.ship_id == ship_id)
        if severity:
            conditions.append(Alert.severity == severity)
        if status:
            conditions.append(Alert.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_active_alerts(self, ship_id: Optional[str] = None) -> List[Alert]:
        """
        Busca alertas ativos.
        
        Args:
            ship_id: Filtrar por navio (opcional)
            
        Returns:
            Lista de alertas ativos
        """
        return await self.list_alerts(
            ship_id=ship_id,
            status=AlertStatus.ACTIVE.value,
            limit=500
        )
    
    async def get_ship_alerts(
        self,
        ship_id: str,
        include_resolved: bool = False
    ) -> List[Alert]:
        """
        Busca alertas de um navio.
        
        Args:
            ship_id: UUID do navio
            include_resolved: Incluir alertas resolvidos
            
        Returns:
            Lista de alertas
        """
        status_filter = None
        if not include_resolved:
            status_filter = AlertStatus.ACTIVE.value
        
        return await self.list_alerts(ship_id=ship_id, status=status_filter)
    
    async def acknowledge(
        self,
        alert_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Reconhece um alerta.
        
        Args:
            alert_id: UUID do alerta
            user_id: UUID do usuário
            notes: Notas opcionais
            
        Returns:
            Alerta atualizado ou None
        """
        alert = await self.get_by_id(alert_id)
        if alert is None:
            return None
        
        alert.acknowledge(user_id, notes)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
    
    async def resolve(self, alert_id: str) -> Optional[Alert]:
        """
        Resolve um alerta.
        
        Args:
            alert_id: UUID do alerta
            
        Returns:
            Alerta atualizado ou None
        """
        alert = await self.get_by_id(alert_id)
        if alert is None:
            return None
        
        alert.resolve()
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
    
    async def create_alert(
        self,
        ship_id: str,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        details: Optional[Dict] = None,
        recommended_actions: Optional[List] = None
    ) -> Alert:
        """
        Cria novo alerta.
        
        Args:
            ship_id: UUID do navio
            alert_type: Tipo do alerta
            severity: Severidade
            title: Título
            message: Mensagem
            details: Detalhes opcionais
            recommended_actions: Ações recomendadas
            
        Returns:
            Alerta criado
        """
        data = {
            "ship_id": ship_id,
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "details": details,
            "recommended_actions": recommended_actions,
            "status": AlertStatus.ACTIVE.value
        }
        
        return await self.create(data)
    
    async def check_existing_alert(
        self,
        ship_id: str,
        alert_type: str
    ) -> Optional[Alert]:
        """
        Verifica se já existe alerta ativo do mesmo tipo.
        
        Args:
            ship_id: UUID do navio
            alert_type: Tipo do alerta
            
        Returns:
            Alerta existente ou None
        """
        query = (
            select(Alert)
            .where(
                and_(
                    Alert.ship_id == ship_id,
                    Alert.alert_type == alert_type,
                    Alert.status == AlertStatus.ACTIVE.value
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def resolve_old_alerts(
        self,
        ship_id: str,
        alert_type: str
    ) -> int:
        """
        Resolve alertas antigos do mesmo tipo.
        
        Args:
            ship_id: UUID do navio
            alert_type: Tipo do alerta
            
        Returns:
            Número de alertas resolvidos
        """
        from sqlalchemy import update
        
        query = (
            update(Alert)
            .where(
                and_(
                    Alert.ship_id == ship_id,
                    Alert.alert_type == alert_type,
                    Alert.status.in_([
                        AlertStatus.ACTIVE.value,
                        AlertStatus.ACKNOWLEDGED.value
                    ])
                )
            )
            .values(
                status=AlertStatus.RESOLVED.value,
                resolved_at=datetime.utcnow()
            )
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount
