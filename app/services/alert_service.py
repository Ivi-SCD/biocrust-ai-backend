"""
Serviço de Alertas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from app.core.alerts.engine import AlertEngine
from app.repositories.alert_repository import AlertRepository
from app.repositories.ship_repository import ShipRepository
from app.repositories.biofouling_repository import BiofoulingRepository

logger = structlog.get_logger()


class AlertService:
    """
    Serviço para gestão de alertas.
    """
    
    def __init__(
        self,
        alert_repo: AlertRepository,
        ship_repo: ShipRepository,
        biofouling_repo: BiofoulingRepository
    ):
        """Inicializa o serviço."""
        self.alert_repo = alert_repo
        self.ship_repo = ship_repo
        self.biofouling_repo = biofouling_repo
        self.engine = AlertEngine()
    
    async def list_alerts(
        self,
        ship_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Lista alertas com filtros.
        
        Args:
            ship_id: Filtrar por navio
            severity: Filtrar por severidade
            status: Filtrar por status
            limit: Limite
            offset: Offset
            
        Returns:
            Dicionário com total e lista de alertas
        """
        logger.info(
            "listing_alerts",
            ship_id=ship_id,
            severity=severity,
            status=status
        )
        
        alerts = await self.alert_repo.list_alerts(
            ship_id=ship_id,
            severity=severity,
            status=status,
            skip=offset,
            limit=limit
        )
        
        total = await self.alert_repo.count_alerts(
            ship_id=ship_id,
            severity=severity,
            status=status
        )
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "id": alert.id,
                "ship_id": alert.ship_id,
                "ship_name": alert.ship.name if alert.ship else "Unknown",
                "severity": alert.severity,
                "type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "details": alert.details,
                "recommended_actions": alert.recommended_actions,
                "created_at": alert.created_at.isoformat(),
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "acknowledged_by": alert.acknowledged_by,
                "status": alert.status
            })
        
        return {
            "total": total,
            "alerts": alerts_data
        }
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Reconhece um alerta.
        
        Args:
            alert_id: UUID do alerta
            user_id: UUID do usuário
            notes: Notas opcionais
            
        Returns:
            Alerta atualizado ou None
        """
        logger.info(
            "acknowledging_alert",
            alert_id=alert_id,
            user_id=user_id
        )
        
        alert = await self.alert_repo.acknowledge(alert_id, user_id, notes)
        if not alert:
            return None
        
        return {
            "id": alert.id,
            "status": alert.status,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "acknowledged_by": alert.acknowledged_by
        }
    
    async def resolve_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve um alerta.
        
        Args:
            alert_id: UUID do alerta
            
        Returns:
            Alerta atualizado ou None
        """
        logger.info("resolving_alert", alert_id=alert_id)
        
        alert = await self.alert_repo.resolve(alert_id)
        if not alert:
            return None
        
        return {
            "id": alert.id,
            "status": alert.status,
            "resolved_at": alert.resolved_at.isoformat()
        }
    
    async def check_ship_alerts(self, ship_id: str) -> List[Dict[str, Any]]:
        """
        Verifica e gera alertas para um navio.
        
        Args:
            ship_id: UUID do navio
            
        Returns:
            Lista de alertas criados
        """
        logger.info("checking_ship_alerts", ship_id=ship_id)
        
        # Buscar dados do navio
        ship = await self.ship_repo.get_with_relations(ship_id)
        if not ship:
            return []
        
        # Buscar índice atual
        latest_index = await self.biofouling_repo.get_latest(ship_id)
        if not latest_index:
            return []
        
        # Buscar métricas ambientais
        metrics = ship.environmental_metrics
        tropical_hours = metrics.tropical_hours if metrics else 0
        total_hours = metrics.total_hours if metrics else 1
        
        # Buscar taxa de degradação
        degradation_rate = await self.biofouling_repo.calculate_degradation_rate(ship_id)
        class_avg_rate = await self.biofouling_repo.get_average_by_class(ship.ship_class)
        
        # Preparar dados para avaliação
        ship_data = {
            "ship_id": ship_id,
            "ship_name": ship.name,
            "index": latest_index.index_value,
            "normam_level": latest_index.normam_level,
            "days_since_cleaning": ship.days_since_cleaning,
            "tropical_hours": tropical_hours,
            "total_hours": total_hours,
            "percentage": (tropical_hours / total_hours * 100) if total_hours > 0 else 0,
            "degradation_rate": degradation_rate,
            "class_avg_rate": class_avg_rate
        }
        
        # Avaliar regras
        alert_data_list = self.engine.evaluate_ship(ship_data)
        
        # Buscar alertas existentes
        existing_alerts = await self.alert_repo.get_active_alerts(ship_id)
        
        # Criar alertas novos
        created_alerts = []
        for alert_data in alert_data_list:
            # Verificar se já existe
            if not self.engine.should_create_alert(
                existing_alerts,
                alert_data["alert_type"]
            ):
                continue
            
            alert = await self.alert_repo.create_alert(
                ship_id=alert_data["ship_id"],
                alert_type=alert_data["alert_type"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                message=alert_data["message"],
                details=alert_data.get("details"),
                recommended_actions=alert_data.get("recommended_actions")
            )
            
            created_alerts.append({
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title
            })
        
        logger.info(
            "ship_alerts_checked",
            ship_id=ship_id,
            alerts_created=len(created_alerts)
        )
        
        return created_alerts
    
    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de regras de alerta.
        
        Returns:
            Lista de definições de regras
        """
        return self.engine.get_rule_definitions()
    
    async def check_fleet_alerts(self) -> Dict[str, Any]:
        """
        Verifica alertas para toda a frota.
        
        Returns:
            Resumo de alertas gerados
        """
        logger.info("checking_fleet_alerts")
        
        ships = await self.ship_repo.get_all(limit=1000)
        
        total_created = 0
        ships_with_alerts = 0
        
        for ship in ships:
            alerts = await self.check_ship_alerts(ship.id)
            if alerts:
                ships_with_alerts += 1
                total_created += len(alerts)
        
        logger.info(
            "fleet_alerts_checked",
            total_ships=len(ships),
            ships_with_alerts=ships_with_alerts,
            total_alerts_created=total_created
        )
        
        return {
            "total_ships_checked": len(ships),
            "ships_with_new_alerts": ships_with_alerts,
            "total_alerts_created": total_created
        }
