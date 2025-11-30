"""
Regras de alerta para bioincrustação.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from app.config import settings


@dataclass
class AlertRule:
    """Definição de uma regra de alerta."""
    
    name: str
    alert_type: str
    severity: str
    condition: Callable[[Dict[str, Any]], bool]
    title_template: str
    message_template: str
    details_builder: Optional[Callable[[Dict[str, Any]], Dict]] = None
    actions_builder: Optional[Callable[[Dict[str, Any]], List[Dict]]] = None
    enabled: bool = True
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            if self.severity == "critical":
                self.notification_channels = ["email", "push", "sms"]
            elif self.severity == "warning":
                self.notification_channels = ["email", "push"]
            else:
                self.notification_channels = ["email"]


def _critical_level_condition(data: Dict[str, Any]) -> bool:
    """Condição para nível crítico."""
    return data.get("normam_level", 0) >= 4 or data.get("index", 0) >= 75


def _critical_level_details(data: Dict[str, Any]) -> Dict:
    """Detalhes para alerta de nível crítico."""
    return {
        "current_index": data.get("index"),
        "normam_level": data.get("normam_level"),
        "days_since_cleaning": data.get("days_since_cleaning"),
        "estimated_additional_cost_per_day": settings.CRITICAL_COST_PER_DAY
    }


def _critical_level_actions(data: Dict[str, Any]) -> List[Dict]:
    """Ações recomendadas para nível crítico."""
    return [
        {
            "action": "schedule_emergency_cleaning",
            "urgency": "immediate",
            "estimated_cost": settings.DEFAULT_CLEANING_COST_BRL * 1.1,  # 10% extra para emergência
            "estimated_savings": settings.CRITICAL_COST_PER_DAY * 30
        }
    ]


def _approaching_critical_condition(data: Dict[str, Any]) -> bool:
    """Condição para aproximando nível crítico."""
    level = data.get("normam_level", 0)
    index = data.get("index", 0)
    return level == 3 or (55 <= index < 75)


def _approaching_critical_details(data: Dict[str, Any]) -> Dict:
    """Detalhes para alerta de aproximação de crítico."""
    return {
        "current_index": data.get("index"),
        "normam_level": data.get("normam_level"),
        "days_since_cleaning": data.get("days_since_cleaning"),
        "estimated_days_to_critical": max(0, int((75 - data.get("index", 0)) / 0.3))
    }


def _approaching_critical_actions(data: Dict[str, Any]) -> List[Dict]:
    """Ações recomendadas para aproximação de crítico."""
    return [
        {
            "action": "schedule_cleaning",
            "urgency": "high",
            "estimated_cost": settings.DEFAULT_CLEANING_COST_BRL,
            "potential_savings": f"Evitar custo adicional de R$ {settings.CRITICAL_COST_PER_DAY}/dia"
        }
    ]


def _tropical_exposure_condition(data: Dict[str, Any]) -> bool:
    """Condição para exposição tropical alta."""
    tropical_hours = data.get("tropical_hours", 0)
    total_hours = data.get("total_hours", 1)
    
    if total_hours == 0:
        return False
    
    return (tropical_hours / total_hours) > 0.7


def _tropical_exposure_details(data: Dict[str, Any]) -> Dict:
    """Detalhes para alerta de exposição tropical."""
    tropical_hours = data.get("tropical_hours", 0)
    total_hours = data.get("total_hours", 1)
    pct = (tropical_hours / total_hours * 100) if total_hours > 0 else 0
    
    return {
        "tropical_hours_30d": tropical_hours,
        "total_hours_30d": total_hours,
        "percentage": round(pct, 1),
        "expected_acceleration": 2.5  # Fator de aceleração
    }


def _tropical_exposure_actions(data: Dict[str, Any]) -> List[Dict]:
    """Ações recomendadas para exposição tropical."""
    return [
        {
            "action": "consider_route_optimization",
            "urgency": "medium",
            "potential_reduction": "25% mais lento na degradação"
        }
    ]


def _degradation_anomaly_condition(data: Dict[str, Any]) -> bool:
    """Condição para anomalia de degradação."""
    rate = data.get("degradation_rate", 0)
    class_avg = data.get("class_avg_rate", 0)
    
    if class_avg == 0:
        return False
    
    return rate > class_avg * 2


def _degradation_anomaly_details(data: Dict[str, Any]) -> Dict:
    """Detalhes para alerta de anomalia de degradação."""
    return {
        "current_rate": data.get("degradation_rate"),
        "class_average_rate": data.get("class_avg_rate"),
        "ratio": round(data.get("degradation_rate", 0) / max(data.get("class_avg_rate", 1), 0.1), 1)
    }


def _degradation_anomaly_actions(data: Dict[str, Any]) -> List[Dict]:
    """Ações recomendadas para anomalia de degradação."""
    return [
        {
            "action": "investigate_cause",
            "urgency": "medium",
            "potential_causes": ["route_profile", "operational_pattern", "hull_damage"]
        }
    ]


# Definição das regras
ALERT_RULES: Dict[str, AlertRule] = {
    "critical_level": AlertRule(
        name="Nível Crítico Atingido",
        alert_type="critical_level_reached",
        severity="critical",
        condition=_critical_level_condition,
        title_template="Nível Crítico de Bioincrustação Atingido",
        message_template="O navio {ship_name} atingiu nível NORMAM {normam_level} (índice {index}). Ação imediata necessária.",
        details_builder=_critical_level_details,
        actions_builder=_critical_level_actions
    ),
    
    "approaching_critical": AlertRule(
        name="Aproximando Nível Crítico",
        alert_type="approaching_critical",
        severity="warning",
        condition=_approaching_critical_condition,
        title_template="Aproximando Nível Crítico de Bioincrustação",
        message_template="O navio {ship_name} está em nível NORMAM {normam_level}. Considere agendar limpeza.",
        details_builder=_approaching_critical_details,
        actions_builder=_approaching_critical_actions
    ),
    
    "tropical_exposure_high": AlertRule(
        name="Exposição Tropical Alta",
        alert_type="tropical_exposure_high",
        severity="warning",
        condition=_tropical_exposure_condition,
        title_template="Alta Exposição a Águas Tropicais",
        message_template="O navio {ship_name} passou {percentage}% do tempo em águas tropicais (lat < 20°).",
        details_builder=_tropical_exposure_details,
        actions_builder=_tropical_exposure_actions
    ),
    
    "degradation_anomaly": AlertRule(
        name="Anomalia de Degradação",
        alert_type="degradation_anomaly",
        severity="warning",
        condition=_degradation_anomaly_condition,
        title_template="Degradação Anômala Detectada",
        message_template="O navio {ship_name} está degradando {ratio}x mais rápido que a média da classe. Investigação recomendada.",
        details_builder=_degradation_anomaly_details,
        actions_builder=_degradation_anomaly_actions
    ),
}


def get_enabled_rules() -> List[AlertRule]:
    """
    Retorna lista de regras habilitadas.
    
    Returns:
        Lista de regras de alerta habilitadas
    """
    return [rule for rule in ALERT_RULES.values() if rule.enabled]


def get_rule_by_type(alert_type: str) -> Optional[AlertRule]:
    """
    Busca regra por tipo de alerta.
    
    Args:
        alert_type: Tipo do alerta
        
    Returns:
        Regra encontrada ou None
    """
    for rule in ALERT_RULES.values():
        if rule.alert_type == alert_type:
            return rule
    return None
