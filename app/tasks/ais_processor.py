"""
Tasks para processamento de dados AIS.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple

import structlog

from app.tasks import celery_app
from app.db.session import async_session_maker
from app.repositories.ais_repository import AISRepository
from app.repositories.ship_repository import ShipRepository

logger = structlog.get_logger()


def run_async(coro):
    """Executa coroutine em task síncrona."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.ais_processor.analyze_environmental_exposure")
def analyze_environmental_exposure(ship_id: str, start_date: str, end_date: str):
    """
    Analisa exposição ambiental de um navio.
    
    Args:
        ship_id: UUID do navio
        start_date: Data inicial (ISO)
        end_date: Data final (ISO)
    """
    logger.info(
        "analyzing_environmental_exposure",
        ship_id=ship_id,
        start_date=start_date,
        end_date=end_date
    )
    
    async def _analyze():
        async with async_session_maker() as session:
            ais_repo = AISRepository(session)
            ship_repo = ShipRepository(session)
            
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            # Calcular horas em cada tipo de água
            tropical, subtropical, temperate = await ais_repo.calculate_water_type_hours(
                ship_id, start, end
            )
            
            # Atualizar métricas do navio
            await ship_repo.update_environmental_metrics(
                ship_id=ship_id,
                period_start=start.date(),
                period_end=end.date(),
                tropical_hours=tropical,
                subtropical_hours=subtropical,
                temperate_hours=temperate
            )
            
            logger.info(
                "environmental_exposure_analyzed",
                ship_id=ship_id,
                tropical_hours=tropical,
                subtropical_hours=subtropical,
                temperate_hours=temperate
            )
            
            return {
                "ship_id": ship_id,
                "tropical_hours": tropical,
                "subtropical_hours": subtropical,
                "temperate_hours": temperate
            }
    
    return run_async(_analyze())


@celery_app.task(name="app.tasks.ais_processor.update_all_environmental_metrics")
def update_all_environmental_metrics():
    """
    Atualiza métricas ambientais de todos os navios.
    
    Executado periodicamente pelo Celery Beat.
    """
    logger.info("updating_all_environmental_metrics")
    
    async def _update_all():
        async with async_session_maker() as session:
            ship_repo = ShipRepository(session)
            ships = await ship_repo.get_all(limit=1000)
            
            updated = 0
            for ship in ships:
                try:
                    # Chamar task de análise para cada navio
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=30)
                    
                    analyze_environmental_exposure.delay(
                        ship.id,
                        start_date.isoformat(),
                        end_date.isoformat()
                    )
                    updated += 1
                    
                except Exception as e:
                    logger.error(
                        "environmental_metrics_update_failed",
                        ship_id=ship.id,
                        error=str(e)
                    )
            
            logger.info(
                "environmental_metrics_update_scheduled",
                total_ships=len(ships),
                tasks_scheduled=updated
            )
            
            return {"tasks_scheduled": updated}
    
    return run_async(_update_all())


@celery_app.task(name="app.tasks.ais_processor.process_ais_batch")
def process_ais_batch(positions: List[dict]):
    """
    Processa batch de posições AIS.
    
    Args:
        positions: Lista de posições para processar
    """
    logger.info(
        "processing_ais_batch",
        num_positions=len(positions)
    )
    
    async def _process():
        async with async_session_maker() as session:
            ais_repo = AISRepository(session)
            
            inserted = await ais_repo.bulk_insert(positions)
            
            logger.info(
                "ais_batch_processed",
                inserted=inserted
            )
            
            return {"inserted": inserted}
    
    return run_async(_process())
