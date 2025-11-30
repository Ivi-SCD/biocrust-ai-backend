"""
Testes unitários para o motor de alertas.
"""

import pytest

from app.core.alerts.engine import AlertEngine
from app.core.alerts.rules import ALERT_RULES, AlertRule


class TestAlertEngine:
    """Testes do motor de alertas."""
    
    @pytest.fixture
    def engine(self):
        """Instância do motor de alertas."""
        return AlertEngine()
    
    def test_engine_initialization(self, engine):
        """Testa inicialização do motor."""
        assert engine is not None
        assert len(engine.rules) > 0
    
    def test_evaluate_ship_critical(self, engine):
        """Testa avaliação de navio em estado crítico."""
        ship_data = {
            "ship_id": "test-id",
            "ship_name": "TEST SHIP",
            "index": 85,
            "normam_level": 4,
            "days_since_cleaning": 300,
            "tropical_hours": 100,
            "total_hours": 720,
            "percentage": 14,
            "degradation_rate": 5,
            "class_avg_rate": 5
        }
        
        alerts = engine.evaluate_ship(ship_data)
        
        assert len(alerts) > 0
        assert any(a["severity"] == "critical" for a in alerts)
    
    def test_evaluate_ship_warning(self, engine):
        """Testa avaliação de navio em estado de alerta."""
        ship_data = {
            "ship_id": "test-id",
            "ship_name": "TEST SHIP",
            "index": 60,
            "normam_level": 3,
            "days_since_cleaning": 150,
            "tropical_hours": 100,
            "total_hours": 720,
            "percentage": 14,
            "degradation_rate": 5,
            "class_avg_rate": 5
        }
        
        alerts = engine.evaluate_ship(ship_data)
        
        assert len(alerts) > 0
        assert any(a["severity"] == "warning" for a in alerts)
    
    def test_evaluate_ship_ok(self, engine):
        """Testa avaliação de navio em estado OK."""
        ship_data = {
            "ship_id": "test-id",
            "ship_name": "TEST SHIP",
            "index": 20,
            "normam_level": 1,
            "days_since_cleaning": 30,
            "tropical_hours": 100,
            "total_hours": 720,
            "percentage": 14,
            "degradation_rate": 3,
            "class_avg_rate": 5
        }
        
        alerts = engine.evaluate_ship(ship_data)
        
        # Não deve ter alertas críticos ou de nível
        critical_alerts = [a for a in alerts if a["alert_type"] in ["critical_level_reached", "approaching_critical"]]
        assert len(critical_alerts) == 0
    
    def test_tropical_exposure_alert(self, engine):
        """Testa alerta de exposição tropical."""
        ship_data = {
            "ship_id": "test-id",
            "ship_name": "TEST SHIP",
            "index": 40,
            "normam_level": 2,
            "days_since_cleaning": 90,
            "tropical_hours": 600,
            "total_hours": 720,
            "percentage": 83,
            "degradation_rate": 5,
            "class_avg_rate": 5
        }
        
        alerts = engine.evaluate_ship(ship_data)
        
        tropical_alerts = [a for a in alerts if a["alert_type"] == "tropical_exposure_high"]
        assert len(tropical_alerts) > 0
    
    def test_degradation_anomaly_alert(self, engine):
        """Testa alerta de anomalia de degradação."""
        ship_data = {
            "ship_id": "test-id",
            "ship_name": "TEST SHIP",
            "index": 50,
            "normam_level": 2,
            "days_since_cleaning": 90,
            "tropical_hours": 200,
            "total_hours": 720,
            "percentage": 28,
            "degradation_rate": 15,  # 3x a média
            "class_avg_rate": 5
        }
        
        alerts = engine.evaluate_ship(ship_data)
        
        anomaly_alerts = [a for a in alerts if a["alert_type"] == "degradation_anomaly"]
        assert len(anomaly_alerts) > 0
    
    def test_get_rule_definitions(self, engine):
        """Testa obtenção de definições de regras."""
        definitions = engine.get_rule_definitions()
        
        assert len(definitions) > 0
        for rule in definitions:
            assert "id" in rule
            assert "name" in rule
            assert "severity" in rule
            assert "enabled" in rule


class TestAlertRules:
    """Testes das regras de alerta."""
    
    def test_all_rules_defined(self):
        """Testa que todas as regras estão definidas."""
        required_rules = [
            "critical_level",
            "approaching_critical",
            "tropical_exposure_high",
            "degradation_anomaly"
        ]
        
        for rule_name in required_rules:
            assert rule_name in ALERT_RULES
    
    def test_rule_structure(self):
        """Testa estrutura das regras."""
        for rule_name, rule in ALERT_RULES.items():
            assert isinstance(rule, AlertRule)
            assert rule.name is not None
            assert rule.alert_type is not None
            assert rule.severity in ["info", "warning", "critical"]
            assert callable(rule.condition)
    
    def test_critical_rule_condition(self):
        """Testa condição de regra crítica."""
        rule = ALERT_RULES["critical_level"]
        
        # Deve disparar
        assert rule.condition({"index": 80, "normam_level": 4})
        assert rule.condition({"index": 75, "normam_level": 3})
        
        # Não deve disparar
        assert not rule.condition({"index": 50, "normam_level": 2})
    
    def test_approaching_critical_condition(self):
        """Testa condição de aproximação de crítico."""
        rule = ALERT_RULES["approaching_critical"]
        
        # Deve disparar
        assert rule.condition({"index": 60, "normam_level": 3})
        
        # Não deve disparar
        assert not rule.condition({"index": 30, "normam_level": 1})
        assert not rule.condition({"index": 80, "normam_level": 4})  # Já é crítico
