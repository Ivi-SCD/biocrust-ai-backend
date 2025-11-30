"""
Motor de geração de alertas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from app.core.alerts.rules import ALERT_RULES, AlertRule, get_enabled_rules
from app.models.alert import Alert, AlertSeverity, AlertStatus

logger = structlog.get_logger()


class AlertEngine:
    """
    Motor de processamento e geração de alertas.
    
    Avalia condições de alerta e gera alertas baseados nas regras definidas.
    """
    
    def __init__(self):
        """Inicializa o motor de alertas."""
        self.rules = get_enabled_rules()
        logger.info(
            "alert_engine_initialized",
            enabled_rules=len(self.rules)
        )
    
    def evaluate_ship(
        self,
        ship_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Avalia todas as regras para um navio.
        
        Args:
            ship_data: Dados do navio para avaliação
            
        Returns:
            Lista de alertas a serem criados
        """
        alerts = []
        
        ship_id = ship_data.get("ship_id")
        ship_name = ship_data.get("ship_name", "Unknown")
        
        logger.debug(
            "evaluating_ship_alerts",
            ship_id=ship_id,
            ship_name=ship_name
        )
        
        for rule in self.rules:
            try:
                if rule.condition(ship_data):
                    alert_data = self._create_alert_data(rule, ship_data)
                    alerts.append(alert_data)
                    
                    logger.info(
                        "alert_triggered",
                        ship_id=ship_id,
                        rule=rule.name,
                        severity=rule.severity
                    )
            except Exception as e:
                logger.error(
                    "alert_evaluation_error",
                    ship_id=ship_id,
                    rule=rule.name,
                    error=str(e)
                )
        
        return alerts
    
    def _create_alert_data(
        self,
        rule: AlertRule,
        ship_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria dados do alerta a partir da regra.
        
        Args:
            rule: Regra que disparou
            ship_data: Dados do navio
            
        Returns:
            Dicionário com dados do alerta
        """
        # Formatar título e mensagem
        title = rule.title_template.format(**ship_data)
        message = rule.message_template.format(**ship_data)
        
        # Construir detalhes
        details = None
        if rule.details_builder:
            details = rule.details_builder(ship_data)
        
        # Construir ações recomendadas
        actions = None
        if rule.actions_builder:
            actions = rule.actions_builder(ship_data)
        
        return {
            "ship_id": ship_data.get("ship_id"),
            "alert_type": rule.alert_type,
            "severity": rule.severity,
            "title": title,
            "message": message,
            "details": details,
            "recommended_actions": actions,
            "status": AlertStatus.ACTIVE.value
        }
    
    def evaluate_fleet(
        self,
        ships_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Avalia alertas para toda a frota.
        
        Args:
            ships_data: Lista com dados de todos os navios
            
        Returns:
            Dicionário mapeando ship_id para lista de alertas
        """
        fleet_alerts = {}
        
        for ship_data in ships_data:
            ship_id = ship_data.get("ship_id")
            alerts = self.evaluate_ship(ship_data)
            
            if alerts:
                fleet_alerts[ship_id] = alerts
        
        logger.info(
            "fleet_evaluation_complete",
            total_ships=len(ships_data),
            ships_with_alerts=len(fleet_alerts),
            total_alerts=sum(len(a) for a in fleet_alerts.values())
        )
        
        return fleet_alerts
    
    def get_rule_definitions(self) -> List[Dict[str, Any]]:
        """
        Retorna definições das regras para exibição na API.
        
        Returns:
            Lista de definições de regras
        """
        definitions = []
        
        for rule_id, rule in ALERT_RULES.items():
            definitions.append({
                "id": rule_id,
                "name": rule.name,
                "condition": self._describe_condition(rule),
                "severity": rule.severity,
                "enabled": rule.enabled,
                "notification_channels": rule.notification_channels
            })
        
        return definitions
    
    def _describe_condition(self, rule: AlertRule) -> str:
        """
        Gera descrição legível da condição.
        
        Args:
            rule: Regra de alerta
            
        Returns:
            Descrição da condição
        """
        descriptions = {
            "critical_level_reached": "index >= 75 OR normam_level >= 4",
            "approaching_critical": "normam_level == 3 OR (55 <= index < 75)",
            "tropical_exposure_high": "tropical_hours / total_hours > 0.7",
            "degradation_anomaly": "degradation_rate > class_avg_rate * 2"
        }
        
        return descriptions.get(rule.alert_type, "Custom condition")
    
    @staticmethod
    def should_create_alert(
        existing_alerts: List[Alert],
        new_alert_type: str
    ) -> bool:
        """
        Verifica se deve criar novo alerta (evita duplicatas).
        
        Args:
            existing_alerts: Alertas existentes do navio
            new_alert_type: Tipo do novo alerta
            
        Returns:
            True se deve criar
        """
        # Verificar se já existe alerta ativo do mesmo tipo
        for alert in existing_alerts:
            if (alert.alert_type == new_alert_type and 
                alert.status == AlertStatus.ACTIVE.value):
                return False
        
        return True
