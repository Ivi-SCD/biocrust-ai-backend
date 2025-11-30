"""
Endpoints de dados AIS.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
import structlog

from app.dependencies import get_ais_service
from app.services.ais_service import AISService
from app.schemas.ais import (
    AISIngestRequest,
    AISIngestResponse,
    TrackResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/ingest",
    response_model=AISIngestResponse,
    summary="Ingerir dados AIS",
    description="Recebe dados AIS em tempo real (webhook para integração externa).",
    responses={
        200: {"description": "Dados aceitos para processamento"},
        400: {"description": "Dados inválidos"}
    }
)
async def ingest_ais_data(
    request: AISIngestRequest,
    ais_service: AISService = Depends(get_ais_service)
):
    """
    Recebe dados AIS em tempo real.
    
    Processo:
    1. Valida dados de entrada
    2. Insere posições no banco (TimescaleDB)
    3. Enfileira task Celery para análise ambiental
    4. Retorna imediatamente
    
    Performance Target: < 50ms (apenas validação e enfileiramento)
    """
    logger.info(
        "ingest_ais_request",
        num_positions=len(request.positions)
    )
    
    positions = [pos.model_dump() for pos in request.positions]
    
    accepted, rejected, processing_id = await ais_service.ingest_positions(
        positions
    )
    
    return AISIngestResponse(
        accepted=accepted,
        rejected=rejected,
        processing_id=processing_id
    )


@router.get(
    "/track/{ship_id}",
    response_model=TrackResponse,
    summary="Trajetória do navio",
    description="Retorna trajetória histórica do navio.",
    responses={
        200: {"description": "Trajetória retornada"},
        404: {"description": "Navio não encontrado"}
    }
)
async def get_ship_track(
    ship_id: str,
    start_date: datetime = Query(..., description="Data inicial (ISO format)"),
    end_date: datetime = Query(..., description="Data final (ISO format)"),
    simplify: bool = Query(
        True,
        description="Simplificar trajetória (Douglas-Peucker)"
    ),
    max_points: int = Query(
        500,
        ge=10,
        le=10000,
        description="Máximo de pontos na resposta"
    ),
    ais_service: AISService = Depends(get_ais_service)
):
    """
    Retorna trajetória histórica do navio.
    
    - **start_date**: Data inicial do período
    - **end_date**: Data final do período
    - **simplify**: Aplicar simplificação de linha
    - **max_points**: Limitar número de pontos
    
    Inclui estatísticas:
    - Distância total
    - Velocidades (média, máxima)
    - Tempo em cada tipo de água
    - Portos visitados
    
    Cache: 6 horas
    """
    logger.info(
        "get_ship_track_request",
        ship_id=ship_id,
        start=start_date,
        end=end_date
    )
    
    result = await ais_service.get_track(
        ship_id=ship_id,
        start_date=start_date,
        end_date=end_date,
        simplify=simplify,
        max_points=max_points
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Navio {ship_id} não encontrado"
        )
    
    return result
