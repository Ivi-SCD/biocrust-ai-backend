"""
Tasks para cálculo de índices de bioincrustação.
"""

import asyncio
from datetime import datetime

import structlog

from app.tasks import celery_app
from app.db.session import async_session_maker
from app.repositories.ship_repository import ShipRepository
from app.repositories.event_repository import EventRepository
from app.repositories.biofouling_repository import BiofoulingRepository
from app.core.biofouling.calculator import BiofoulingCalculator

logger = structlog.get_logger()


def run_async(coro):
    """Executa coroutine em task síncrona."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.index_calculator.calculate_ship_index")
def calculate_ship_index(ship_id: str):
    """
    Calcula índice de bioincrustação para um navio.
    
    Args:
        ship_id: UUID do navio
    """
    logger.info("calculating_ship_index", ship_id=ship_id)
    
    async def _calculate():
        async with async_session_maker() as session:
            ship_repo = ShipRepository(session)
            event_repo = EventRepository(session)
            biofouling_repo = BiofoulingRepository(session)
            
            # Buscar navio
            ship = await ship_repo.get_by_id(ship_id)
            if not ship:
                logger.warning("ship_not_found", ship_id=ship_id)
                return None
            
            # Buscar eventos recentes
            events = await event_repo.get_events_for_calculation(ship_id, limit=30)
            if not events:
                logger.warning("no_events_for_calculation", ship_id=ship_id)
                return None
            
            # Converter eventos para formato do calculador
            events_data = []
            for event in events:
                events_data.append({
                    "ship_name": ship.name,
                    "ship_class": ship.ship_class,
                    "start_date": event.start_date,
                    "end_date": event.end_date,
                    "distance_nm": event.distance_nm,
                    "duration_hours": event.duration_hours,
                    "speed": event.avg_speed,
                    "displacement": event.displacement,
                    "aft_draft": event.aft_draft,
                    "fwd_draft": event.fwd_draft,
                    "mid_draft": event.mid_draft,
                    "trim": event.trim,
                    "beaufort_scale": event.beaufort_scale or 3,
                    "latitude": event.latitude or -23,
                    "longitude": event.longitude or -45,
                })
            
            # Calcular índice
            calculator = BiofoulingCalculator()
            results = calculator.calculate_from_events(
                events_data,
                ship_length_m=ship.length_m
            )
            
            if not results:
                return None
            
            # Pegar resultado mais recente
            latest = results[-1]
            
            # Salvar no banco
            index_data = {
                "ship_id": ship_id,
                "calculated_at": datetime.utcnow(),
                "index_value": latest["index"],
                "normam_level": latest["normam_level"],
                "component_efficiency": latest["components"]["efficiency"],
                "component_environmental": latest["components"]["environmental"],
                "component_temporal": latest["components"]["temporal"],
                "component_operational": latest["components"]["operational"],
            }
            
            record = await biofouling_repo.create(index_data)
            
            logger.info(
                "ship_index_calculated",
                ship_id=ship_id,
                index=latest["index"],
                level=latest["normam_level"]
            )
            
            return {
                "ship_id": ship_id,
                "index": latest["index"],
                "normam_level": latest["normam_level"],
                "record_id": record.id
            }
    
    return run_async(_calculate())


@celery_app.task(name="app.tasks.index_calculator.calculate_fleet_indices")
def calculate_fleet_indices():
    """
    Calcula índices para toda a frota.
    
    Executado periodicamente pelo Celery Beat.
    """
    logger.info("calculating_fleet_indices")
    
    async def _calculate_all():
        async with async_session_maker() as session:
            ship_repo = ShipRepository(session)
            ships = await ship_repo.get_all(limit=1000)
            
            scheduled = 0
            for ship in ships:
                try:
                    calculate_ship_index.delay(ship.id)
                    scheduled += 1
                except Exception as e:
                    logger.error(
                        "index_calculation_schedule_failed",
                        ship_id=ship.id,
                        error=str(e)
                    )
            
            logger.info(
                "fleet_indices_calculation_scheduled",
                total_ships=len(ships),
                tasks_scheduled=scheduled
            )
            
            return {"tasks_scheduled": scheduled}
    
    return run_async(_calculate_all())
