"""
Endpoints de Bioincrustação.
"""

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.dependencies import get_biofouling_service
from app.services.biofouling_service import BiofoulingService
from app.schemas.biofouling import (
    BiofoulingCalculateRequest,
    BiofoulingCalculateResponse,
    FleetSummaryResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/calculate",
    response_model=BiofoulingCalculateResponse,
    summary="Calcular índice de bioincrustação",
    description="Calcula índice de bioincrustação para eventos de navegação fornecidos.",
    responses={
        200: {"description": "Índices calculados"},
        400: {"description": "Dados inválidos"},
        500: {"description": "Erro de cálculo"}
    }
)
async def calculate_biofouling(
    request: BiofoulingCalculateRequest,
    biofouling_service: BiofoulingService = Depends(get_biofouling_service)
):
    """
    Calcula índice de bioincrustação para uma lista de eventos de navegação.
    
    O cálculo usa o modelo físico-estatístico baseado em:
    - Eficiência hidrodinâmica
    - Exposição ambiental
    - Acúmulo temporal
    - Condições operacionais
    
    **Não usa cache** - sempre cálculo fresco.
    
    Performance Target: < 200ms para batch de 100 eventos.
    """
    logger.info(
        "calculate_biofouling_request",
        num_events=len(request.events)
    )
    
    try:
        # Converter eventos para formato esperado
        events = [event.model_dump() for event in request.events]
        
        results = await biofouling_service.calculate_index(
            events=events,
            ship_length_m=request.ship_length_m
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error("biofouling_calculation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular índice: {str(e)}"
        )


@router.get(
    "/fleet-summary",
    response_model=FleetSummaryResponse,
    summary="Resumo executivo da frota",
    description="Retorna resumo executivo de toda a frota com estatísticas de bioincrustação.",
    responses={
        200: {"description": "Resumo da frota"},
        500: {"description": "Erro interno"}
    }
)
async def get_fleet_summary(
    biofouling_service: BiofoulingService = Depends(get_biofouling_service)
):
    """
    Gera resumo executivo de toda a frota.
    
    Inclui:
    - Distribuição por status (ok, warning, critical)
    - Distribuição por nível NORMAM (0-4)
    - Índice médio da frota
    - Piores e melhores navios
    - Impacto de custo mensal estimado
    
    Cache: 10 minutos
    """
    logger.info("get_fleet_summary_request")
    
    result = await biofouling_service.get_fleet_summary()
    
    return result
