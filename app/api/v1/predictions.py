"""
Endpoints de Previsões.
"""

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.dependencies import get_biofouling_service
from app.services.biofouling_service import BiofoulingService
from app.schemas.prediction import (
    ForecastRequest,
    ForecastResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    summary="Gerar previsão de degradação",
    description="Gera previsão temporal de degradação do índice de bioincrustação.",
    responses={
        200: {"description": "Previsão gerada"},
        404: {"description": "Navio não encontrado"},
        500: {"description": "Erro de previsão"}
    }
)
async def generate_forecast(
    request: ForecastRequest,
    biofouling_service: BiofoulingService = Depends(get_biofouling_service)
):
    """
    Gera previsão de degradação futura.
    
    Cenários disponíveis:
    - **current_pattern**: Mantém padrão operacional atual
    - **tropical_route**: Rotas predominantemente tropicais
    - **temperate_route**: Rotas predominantemente temperadas
    - **cleaning_at_day**: Simula limpeza em um dia específico
    
    O modelo usa:
    - Taxa base de crescimento calibrada
    - Fator de aceleração tropical
    - Curva logarítmica de crescimento
    
    Cache: 1 hora (invalidado com novos dados)
    """
    logger.info(
        "generate_forecast_request",
        ship_id=request.ship_id,
        days=request.forecast_days
    )
    
    scenarios_dict = {
        "current_pattern": request.scenarios.current_pattern,
        "tropical_route": request.scenarios.tropical_route,
        "temperate_route": request.scenarios.temperate_route,
    }
    
    if request.scenarios.cleaning_at_day is not None:
        scenarios_dict["cleaning_at_day"] = request.scenarios.cleaning_at_day
    
    result = await biofouling_service.generate_forecast(
        ship_id=request.ship_id,
        forecast_days=request.forecast_days,
        scenarios=scenarios_dict
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Navio {request.ship_id} não encontrado ou sem dados"
        )
    
    return result
