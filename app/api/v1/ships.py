"""
Endpoints de Navios.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
import structlog

from app.dependencies import get_ship_service
from app.services.ship_service import ShipService
from app.schemas.ship import (
    ShipListResponse,
    ShipDetailResponse,
    ShipTimelineResponse,
    ShipFilterParams,
    ShipStatus,
    TimelineInterval,
)

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "",
    response_model=ShipListResponse,
    summary="Listar navios",
    description="Lista todos os navios com status atual de bioincrustação.",
    responses={
        200: {"description": "Lista de navios"},
        500: {"description": "Erro interno"}
    }
)
async def list_ships(
    status: Optional[ShipStatus] = Query(
        None,
        description="Filtrar por status (ok, warning, critical)"
    ),
    ship_class: Optional[str] = Query(
        None,
        alias="class",
        description="Filtrar por classe (Aframax, Suezmax, etc)"
    ),
    sort_by: str = Query(
        "name",
        description="Campo para ordenação (index, name, last_inspection)"
    ),
    order: str = Query(
        "asc",
        regex="^(asc|desc)$",
        description="Ordem de ordenação"
    ),
    limit: int = Query(50, ge=1, le=500, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    ship_service: ShipService = Depends(get_ship_service)
):
    """
    Lista todos os navios da frota com status de bioincrustação.
    
    - **status**: Filtrar por status de bioincrustação
    - **class**: Filtrar por classe do navio
    - **sort_by**: Campo para ordenação
    - **order**: Direção da ordenação
    - **limit**: Número máximo de resultados
    - **offset**: Deslocamento para paginação
    
    Cache: 5 minutos
    """
    logger.info(
        "list_ships_request",
        status=status,
        ship_class=ship_class
    )
    
    params = ShipFilterParams(
        status=status,
        ship_class=ship_class,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset
    )
    
    result = await ship_service.list_ships(params)
    
    return result


@router.get(
    "/{ship_id}",
    response_model=ShipDetailResponse,
    summary="Detalhes do navio",
    description="Retorna detalhes completos de um navio específico.",
    responses={
        200: {"description": "Detalhes do navio"},
        404: {"description": "Navio não encontrado"}
    }
)
async def get_ship(
    ship_id: str,
    ship_service: ShipService = Depends(get_ship_service)
):
    """
    Busca detalhes completos de um navio.
    
    Inclui:
    - Especificações técnicas
    - Status atual de bioincrustação
    - Posição atual
    - Eventos recentes
    - Histórico de índices
    - Alertas ativos
    
    Cache: 2 minutos
    """
    logger.info("get_ship_request", ship_id=ship_id)
    
    result = await ship_service.get_ship_detail(ship_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Navio {ship_id} não encontrado"
        )
    
    return result


@router.get(
    "/{ship_id}/timeline",
    response_model=ShipTimelineResponse,
    summary="Timeline do navio",
    description="Retorna timeline detalhado de evolução do índice.",
    responses={
        200: {"description": "Timeline do navio"},
        404: {"description": "Navio não encontrado"}
    }
)
async def get_ship_timeline(
    ship_id: str,
    start_date: datetime = Query(..., description="Data inicial (ISO format)"),
    end_date: datetime = Query(..., description="Data final (ISO format)"),
    interval: TimelineInterval = Query(
        TimelineInterval.DAY,
        description="Intervalo de agregação"
    ),
    ship_service: ShipService = Depends(get_ship_service)
):
    """
    Busca timeline detalhado de evolução do índice de bioincrustação.
    
    - **start_date**: Data inicial do período
    - **end_date**: Data final do período
    - **interval**: Intervalo de agregação (day, week, month)
    
    Cache: 1 hora
    """
    logger.info(
        "get_ship_timeline_request",
        ship_id=ship_id,
        start=start_date,
        end=end_date
    )
    
    result = await ship_service.get_ship_timeline(
        ship_id=ship_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval.value
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Navio {ship_id} não encontrado"
        )
    
    return result
