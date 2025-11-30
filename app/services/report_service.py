"""
Serviço de Relatórios.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog

from app.config import settings
from app.models.report import Report, ReportStatus, ReportType
from app.repositories.ship_repository import ShipRepository
from app.repositories.biofouling_repository import BiofoulingRepository
from app.repositories.alert_repository import AlertRepository

logger = structlog.get_logger()


class ReportService:
    """
    Serviço para geração de relatórios.
    """
    
    def __init__(
        self,
        ship_repo: ShipRepository,
        biofouling_repo: BiofoulingRepository,
        alert_repo: AlertRepository
    ):
        """Inicializa o serviço."""
        self.ship_repo = ship_repo
        self.biofouling_repo = biofouling_repo
        self.alert_repo = alert_repo
    
    async def create_report_request(
        self,
        report_type: str,
        parameters: Dict[str, Any],
        requested_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria solicitação de relatório.
        
        Args:
            report_type: Tipo do relatório
            parameters: Parâmetros do relatório
            requested_by: UUID do solicitante
            
        Returns:
            Dados do relatório criado
        """
        report_id = str(uuid4())
        
        logger.info(
            "creating_report_request",
            report_id=report_id,
            type=report_type
        )
        
        # Estimar tempo de conclusão
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)
        
        return {
            "report_id": report_id,
            "status": "processing",
            "estimated_completion": estimated_completion.isoformat(),
            "webhook_url": None  # TODO: implementar webhooks
        }
    
    async def get_report_status(
        self,
        report_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca status do relatório.
        
        Args:
            report_id: UUID do relatório
            
        Returns:
            Status ou None
        """
        # TODO: implementar persistência de relatórios
        # Por ora, retornar status simulado
        
        return {
            "report_id": report_id,
            "status": "completed",
            "progress_pct": 100,
            "current_step": "Concluído",
            "download_url": f"/api/v1/reports/{report_id}/download",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "metadata": {
                "pages": 24,
                "generated_at": datetime.utcnow().isoformat(),
                "file_size_bytes": 2458624
            }
        }
    
    async def generate_executive_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        ship_classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gera dados para relatório executivo.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            ship_classes: Classes a incluir
            
        Returns:
            Dados do relatório
        """
        logger.info(
            "generating_executive_summary",
            start=start_date,
            end=end_date
        )
        
        # Buscar estatísticas
        stats = await self.biofouling_repo.get_fleet_summary_stats()
        
        # Buscar piores navios
        worst = await self.biofouling_repo.get_worst_ships(10)
        best = await self.biofouling_repo.get_best_ships(10)
        
        # Buscar alertas do período
        critical_alerts = await self.alert_repo.count_alerts(severity="critical")
        warning_alerts = await self.alert_repo.count_alerts(severity="warning")
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "fleet_overview": {
                "total_ships": stats["total"],
                "average_index": stats["avg_index"],
                "status_distribution": stats["status_distribution"],
                "level_distribution": stats["level_distribution"]
            },
            "critical_situations": {
                "critical_alerts": critical_alerts,
                "warning_alerts": warning_alerts
            },
            "top_performers": [
                {
                    "ship_id": idx.ship_id,
                    "index": idx.index_value,
                    "level": idx.normam_level
                }
                for idx in best
            ],
            "worst_performers": [
                {
                    "ship_id": idx.ship_id,
                    "index": idx.index_value,
                    "level": idx.normam_level
                }
                for idx in worst
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
