"""
Tasks para verificação de alertas.
"""

import asyncio

import structlog

from app.tasks import celery_app
from app.db.session import async_session_maker
from app.repositories.ship_repository import ShipRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.biofouling_repository import BiofoulingRepository
from app.core.alerts.engine import AlertEngine

logger = structlog.get_logger()


def run_async(coro):
    """Executa coroutine em task síncrona."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.alert_checker.check_ship_alerts")
def check_ship_alerts(ship_id: str):
    """
    Verifica alertas para um navio específico.
    
    Args:
        ship_id: UUID do navio
    """
    logger.info("checking_ship_alerts", ship_id=ship_id)
    
    async def _check():
        async with async_session_maker() as session:
            ship_repo = ShipRepository(session)
            alert_repo = AlertRepository(session)
            biofouling_repo = BiofoulingRepository(session)
            engine = AlertEngine()
            
            # Buscar dados do navio
            ship = await ship_repo.get_with_relations(ship_id)
            if not ship:
                logger.warning("ship_not_found", ship_id=ship_id)
                return None
            
            # Buscar índice atual
            latest_index = await biofouling_repo.get_latest(ship_id)
            if not latest_index:
                return {"ship_id": ship_id, "alerts_created": 0}
            
            # Buscar métricas ambientais
            metrics = ship.environmental_metrics
            tropical_hours = metrics.tropical_hours if metrics else 0
            total_hours = metrics.total_hours if metrics else 1
            
            # Calcular taxa de degradação
            degradation_rate = await biofouling_repo.calculate_degradation_rate(ship_id)
            class_avg_rate = await biofouling_repo.get_average_by_class(ship.ship_class)
            
            # Preparar dados
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
            alert_data_list = engine.evaluate_ship(ship_data)
            
            # Buscar alertas existentes
            existing_alerts = await alert_repo.get_active_alerts(ship_id)
            
            # Criar alertas novos
            created = 0
            for alert_data in alert_data_list:
                if not engine.should_create_alert(existing_alerts, alert_data["alert_type"]):
                    continue
                
                await alert_repo.create_alert(
                    ship_id=alert_data["ship_id"],
                    alert_type=alert_data["alert_type"],
                    severity=alert_data["severity"],
                    title=alert_data["title"],
                    message=alert_data["message"],
                    details=alert_data.get("details"),
                    recommended_actions=alert_data.get("recommended_actions")
                )
                created += 1
            
            logger.info(
                "ship_alerts_checked",
                ship_id=ship_id,
                alerts_created=created
            )
            
            return {"ship_id": ship_id, "alerts_created": created}
    
    return run_async(_check())


@celery_app.task(name="app.tasks.alert_checker.check_fleet_alerts")
def check_fleet_alerts():
    """
    Verifica alertas para toda a frota.
    
    Executado periodicamente pelo Celery Beat (a cada hora).
    """
    logger.info("checking_fleet_alerts")
    
    async def _check_all():
        async with async_session_maker() as session:
            ship_repo = ShipRepository(session)
            ships = await ship_repo.get_all(limit=1000)
            
            scheduled = 0
            for ship in ships:
                try:
                    check_ship_alerts.delay(ship.id)
                    scheduled += 1
                except Exception as e:
                    logger.error(
                        "alert_check_schedule_failed",
                        ship_id=ship.id,
                        error=str(e)
                    )
            
            logger.info(
                "fleet_alerts_check_scheduled",
                total_ships=len(ships),
                tasks_scheduled=scheduled
            )
            
            return {"tasks_scheduled": scheduled}
    
    return run_async(_check_all())
