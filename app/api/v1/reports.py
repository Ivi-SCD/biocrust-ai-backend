"""
Endpoints de Relatórios.
"""

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.dependencies import get_report_service
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportStatusResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/generate",
    response_model=ReportGenerateResponse,
    summary="Gerar relatório",
    description="Solicita geração de relatório customizado (assíncrono).",
    responses={
        200: {"description": "Relatório em geração"},
        400: {"description": "Parâmetros inválidos"}
    }
)
async def generate_report(
    request: ReportGenerateRequest,
    report_service: ReportService = Depends(get_report_service)
):
    """
    Solicita geração de relatório customizado.
    
    Tipos disponíveis:
    - **executive_summary**: Resumo executivo
    - **fleet_analysis**: Análise detalhada da frota
    - **ship_detail**: Detalhes de um navio
    - **cost_analysis**: Análise de custos
    - **sustainability**: Impacto ambiental
    
    A geração é assíncrona. Use GET /reports/{report_id} para verificar status.
    """
    logger.info(
        "generate_report_request",
        type=request.report_type,
        format=request.format
    )
    
    result = await report_service.create_report_request(
        report_type=request.report_type,
        parameters=request.model_dump(),
        requested_by=None  # TODO: pegar do token
    )
    
    return result


@router.get(
    "/{report_id}",
    response_model=ReportStatusResponse,
    summary="Status do relatório",
    description="Verifica status e obtém relatório.",
    responses={
        200: {"description": "Status do relatório"},
        404: {"description": "Relatório não encontrado"}
    }
)
async def get_report_status(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """
    Verifica status de geração do relatório.
    
    Status possíveis:
    - **pending**: Aguardando processamento
    - **processing**: Em geração
    - **completed**: Pronto para download
    - **failed**: Falha na geração
    
    Quando completed, inclui URL de download.
    """
    logger.info("get_report_status_request", report_id=report_id)
    
    result = await report_service.get_report_status(report_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relatório {report_id} não encontrado"
        )
    
    return result
