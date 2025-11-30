"""
Tasks para geração de relatórios.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from app.tasks import celery_app
from app.config import settings

logger = structlog.get_logger()


def run_async(coro):
    """Executa coroutine em task síncrona."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.report_generator.generate_report")
def generate_report(report_id: str, report_type: str, parameters: dict):
    """
    Gera um relatório.
    
    Args:
        report_id: UUID do relatório
        report_type: Tipo do relatório
        parameters: Parâmetros de geração
    """
    logger.info(
        "generating_report",
        report_id=report_id,
        type=report_type
    )
    
    try:
        # Simular geração (implementação real usaria ReportLab/Jinja2)
        # TODO: implementar geração real de PDF
        
        # Criar diretório de relatórios
        reports_dir = Path(settings.REPORTS_STORAGE_PATH)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Simular arquivo
        file_path = reports_dir / f"{report_id}.pdf"
        file_path.touch()
        
        logger.info(
            "report_generated",
            report_id=report_id,
            file_path=str(file_path)
        )
        
        return {
            "report_id": report_id,
            "status": "completed",
            "file_path": str(file_path),
            "download_url": f"/api/v1/reports/{report_id}/download",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
    except Exception as e:
        logger.error(
            "report_generation_failed",
            report_id=report_id,
            error=str(e)
        )
        return {
            "report_id": report_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="app.tasks.report_generator.cleanup_expired_reports")
def cleanup_expired_reports():
    """
    Remove relatórios expirados.
    
    Executado diariamente pelo Celery Beat.
    """
    logger.info("cleaning_up_expired_reports")
    
    reports_dir = Path(settings.REPORTS_STORAGE_PATH)
    if not reports_dir.exists():
        return {"removed": 0}
    
    removed = 0
    expiry_threshold = datetime.utcnow() - timedelta(days=settings.REPORTS_EXPIRY_DAYS)
    
    for file in reports_dir.iterdir():
        if file.is_file():
            # Verificar data de modificação
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < expiry_threshold:
                file.unlink()
                removed += 1
    
    logger.info("expired_reports_cleaned", removed=removed)
    
    return {"removed": removed}
