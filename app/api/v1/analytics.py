"""
Endpoints de Analytics.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
import structlog

from app.dependencies import get_ship_service, get_biofouling_service
from app.services.ship_service import ShipService
from app.services.biofouling_service import BiofoulingService
from app.schemas.analytics import (
    FleetTrendsResponse,
    BenchmarkingRequest,
    BenchmarkingResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/fleet-trends",
    response_model=FleetTrendsResponse,
    summary="Tendências da frota",
    description="Análise de tendências da frota.",
    responses={
        200: {"description": "Análise de tendências"}
    }
)
async def get_fleet_trends(
    period: str = Query(
        "last_30d",
        regex="^(last_7d|last_30d|last_90d|last_year)$",
        description="Período de análise"
    ),
    metric: str = Query(
        "index",
        regex="^(index|efficiency|fuel_consumption)$",
        description="Métrica a analisar"
    ),
    group_by: str = Query(
        "class",
        regex="^(class|status)$",
        description="Agrupamento"
    ),
    biofouling_service: BiofoulingService = Depends(get_biofouling_service)
):
    """
    Análise de tendências da frota.
    
    - **period**: Período de análise (7d, 30d, 90d, 1 ano)
    - **metric**: Métrica (índice, eficiência, consumo)
    - **group_by**: Agrupamento (classe ou status)
    
    Inclui:
    - Agregação da frota
    - Análise por classe/status
    - Correlações
    - Insights automatizados
    
    Cache: 1 hora
    """
    logger.info(
        "get_fleet_trends_request",
        period=period,
        metric=metric,
        group_by=group_by
    )
    
    # TODO: implementar análise completa
    # Por ora, retornar dados simulados
    
    return FleetTrendsResponse(
        period=period,
        metric=metric,
        fleet_aggregate={
            "current_avg": 48.3,
            "previous_period_avg": 42.1,
            "change_pct": 14.7,
            "trend": "worsening"
        },
        by_class=[
            {
                "class": "Aframax",
                "ship_count": 12,
                "avg_index": 45.2,
                "trend": "stable",
                "best_performer": "HENRIQUE ALVES",
                "worst_performer": "CARLA SILVA"
            },
            {
                "class": "Suezmax",
                "ship_count": 15,
                "avg_index": 52.1,
                "trend": "improving"
            }
        ],
        correlations={
            "tropical_exposure_vs_index": 0.78,
            "avg_speed_vs_index": -0.42,
            "days_since_cleaning_vs_index": 0.91
        },
        insights=[]
    )


@router.get(
    "/benchmarking",
    response_model=BenchmarkingResponse,
    summary="Benchmarking de navios",
    description="Comparação entre navios similares.",
    responses={
        200: {"description": "Análise de benchmarking"},
        404: {"description": "Navio não encontrado"}
    }
)
async def get_benchmarking(
    ship_id: str = Query(..., description="UUID do navio de referência"),
    comparison_group: str = Query(
        "same_class",
        regex="^(same_class|same_age|custom_list)$",
        description="Grupo de comparação"
    ),
    biofouling_service: BiofoulingService = Depends(get_biofouling_service)
):
    """
    Comparação entre navios similares.
    
    - **ship_id**: Navio de referência
    - **comparison_group**: Grupo para comparação
    
    Inclui:
    - Ranking do navio
    - Comparação detalhada
    - Oportunidades de melhoria
    
    Cache: 2 horas
    """
    logger.info(
        "get_benchmarking_request",
        ship_id=ship_id,
        group=comparison_group
    )
    
    # TODO: implementar benchmarking completo
    # Por ora, retornar dados simulados
    
    return BenchmarkingResponse(
        reference_ship={
            "id": ship_id,
            "name": "BRUNO LIMA",
            "class": "Gaseiros 7k",
            "index": 67.4
        },
        comparison_group={
            "ships_count": 4,
            "avg_index": 48.2,
            "median_index": 45.7
        },
        ranking={
            "position": 4,
            "percentile": 25,
            "interpretation": "Pior que 75% dos navios similares"
        },
        detailed_comparison=[
            {
                "ship_name": "FÁBIO SANTOS",
                "index": 28.4,
                "delta": -39.0,
                "factors": {
                    "better_route_planning": True,
                    "more_frequent_cleaning": True,
                    "better_operational_efficiency": True
                }
            }
        ],
        improvement_opportunities=[
            {
                "area": "route_optimization",
                "potential_improvement_pct": 25,
                "estimated_value_brl": 180000
            }
        ]
    )
