"""
Endpoints de Alertas.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
import structlog

from app.dependencies import get_alert_service
from app.services.alert_service import AlertService
from app.schemas.alert import (
    AlertListResponse,
    AlertResponse,
    AlertAcknowledgeRequest,
    AlertRulesListResponse,
)
from app.schemas.common import MessageResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "",
    response_model=AlertListResponse,
    summary="Listar alertas",
    description="Lista todos os alertas com filtros opcionais.",
    responses={
        200: {"description": "Lista de alertas"}
    }
)
async def list_alerts(
    severity: Optional[str] = Query(
        None,
        description="Filtrar por severidade (critical, warning, info)"
    ),
    ship_id: Optional[str] = Query(
        None,
        description="Filtrar por navio"
    ),
    alert_status: Optional[str] = Query(
        None,
        alias="status",
        description="Filtrar por status (active, acknowledged, resolved)"
    ),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Lista alertas com filtros opcionais.
    
    - **severity**: Filtrar por severidade
    - **ship_id**: Filtrar por navio específico
    - **status**: Filtrar por status do alerta
    
    **Sem cache** - sempre em tempo real.
    """
    logger.info(
        "list_alerts_request",
        severity=severity,
        ship_id=ship_id,
        status=alert_status
    )
    
    result = await alert_service.list_alerts(
        ship_id=ship_id,
        severity=severity,
        status=alert_status,
        limit=limit,
        offset=offset
    )
    
    return result


@router.post(
    "/{alert_id}/acknowledge",
    response_model=MessageResponse,
    summary="Reconhecer alerta",
    description="Marca um alerta como reconhecido.",
    responses={
        200: {"description": "Alerta reconhecido"},
        404: {"description": "Alerta não encontrado"}
    }
)
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Marca um alerta como reconhecido.
    
    Permite adicionar notas sobre a ação tomada.
    """
    logger.info(
        "acknowledge_alert_request",
        alert_id=alert_id,
        user_id=request.acknowledged_by
    )
    
    result = await alert_service.acknowledge_alert(
        alert_id=alert_id,
        user_id=request.acknowledged_by,
        notes=request.notes
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerta {alert_id} não encontrado"
        )
    
    return MessageResponse(
        message=f"Alerta {alert_id} reconhecido com sucesso",
        success=True
    )


@router.post(
    "/{alert_id}/resolve",
    response_model=MessageResponse,
    summary="Resolver alerta",
    description="Marca um alerta como resolvido.",
    responses={
        200: {"description": "Alerta resolvido"},
        404: {"description": "Alerta não encontrado"}
    }
)
async def resolve_alert(
    alert_id: str,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Marca um alerta como resolvido.
    """
    logger.info("resolve_alert_request", alert_id=alert_id)
    
    result = await alert_service.resolve_alert(alert_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerta {alert_id} não encontrado"
        )
    
    return MessageResponse(
        message=f"Alerta {alert_id} resolvido com sucesso",
        success=True
    )


@router.get(
    "/rules",
    response_model=AlertRulesListResponse,
    summary="Listar regras de alerta",
    description="Lista todas as regras de alerta configuradas.",
    responses={
        200: {"description": "Lista de regras"}
    }
)
async def get_alert_rules(
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Lista regras de alerta configuradas.
    
    Retorna:
    - Nome da regra
    - Condição de disparo
    - Severidade
    - Status (habilitada/desabilitada)
    - Canais de notificação
    """
    logger.info("get_alert_rules_request")
    
    rules = await alert_service.get_alert_rules()
    
    return {"rules": rules}


@router.post(
    "/check/{ship_id}",
    summary="Verificar alertas de um navio",
    description="Executa verificação de alertas para um navio específico.",
    responses={
        200: {"description": "Alertas verificados"},
        404: {"description": "Navio não encontrado"}
    }
)
async def check_ship_alerts(
    ship_id: str,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Executa verificação de alertas para um navio.
    
    Avalia todas as regras e cria alertas se necessário.
    """
    logger.info("check_ship_alerts_request", ship_id=ship_id)
    
    created = await alert_service.check_ship_alerts(ship_id)
    
    return {
        "ship_id": ship_id,
        "alerts_created": len(created),
        "alerts": created
    }
