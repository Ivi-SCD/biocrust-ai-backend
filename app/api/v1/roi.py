"""
Endpoints de ROI.
"""

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.dependencies import get_biofouling_service
from app.services.biofouling_service import BiofoulingService
from app.schemas.roi import (
    ROICalculateRequest,
    ROICalculateResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/calculate",
    response_model=ROICalculateResponse,
    summary="Calcular ROI de estratégias",
    description="Calcula ROI de diferentes estratégias de manutenção.",
    responses={
        200: {"description": "ROI calculado"},
        404: {"description": "Navio não encontrado"},
        500: {"description": "Erro de cálculo"}
    }
)
async def calculate_roi(
    request: ROICalculateRequest,
    biofouling_service: BiofoulingService = Depends(get_biofouling_service)
):
    """
    Calcula retorno sobre investimento de estratégias de limpeza.
    
    Para cada estratégia, calcula:
    - **Custos**: limpeza + downtime + combustível adicional
    - **Economias**: combustível economizado após limpeza
    - **ROI %**: percentual de retorno
    - **Payback**: dias para recuperar investimento
    - **NPV**: valor presente líquido em 12 meses
    
    Inclui análise de sensibilidade para variação de preço de combustível.
    
    Cache: 30 minutos
    """
    logger.info(
        "calculate_roi_request",
        ship_id=request.ship_id,
        num_strategies=len(request.strategies)
    )
    
    strategies = [s.model_dump() for s in request.strategies]
    
    result = await biofouling_service.calculate_roi(
        ship_id=request.ship_id,
        strategies=strategies,
        fuel_price_per_ton=request.fuel_price_per_ton,
        operational_days_per_year=request.operational_days_per_year,
        downtime_cost_per_day=request.downtime_cost_per_day
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Navio {request.ship_id} não encontrado ou sem dados"
        )
    
    return result
