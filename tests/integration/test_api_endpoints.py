"""
Testes de integração dos endpoints da API.
"""

import pytest
from datetime import datetime, timedelta


class TestHealthEndpoints:
    """Testes dos endpoints de health."""
    
    def test_root_endpoint(self, client):
        """Testa endpoint raiz."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_endpoint(self, client):
        """Testa endpoint de health."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestShipsEndpoints:
    """Testes dos endpoints de navios."""
    
    def test_list_ships_empty(self, client):
        """Testa listagem de navios vazia."""
        response = client.get("/api/v1/ships")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "ships" in data
    
    def test_list_ships_with_filters(self, client):
        """Testa listagem com filtros."""
        response = client.get("/api/v1/ships?class=Aframax&limit=10")
        
        assert response.status_code == 200
    
    def test_get_ship_not_found(self, client):
        """Testa busca de navio inexistente."""
        response = client.get("/api/v1/ships/non-existent-id")
        
        assert response.status_code == 404


class TestBiofoulingEndpoints:
    """Testes dos endpoints de bioincrustação."""
    
    def test_calculate_biofouling(self, client, sample_event_data):
        """Testa cálculo de bioincrustação."""
        response = client.post(
            "/api/v1/biofouling/calculate",
            json={"events": [sample_event_data]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        
        result = data["results"][0]
        assert "index" in result
        assert "normam_level" in result
        assert "status" in result
    
    def test_calculate_biofouling_batch(self, client, sample_event_data):
        """Testa cálculo em batch."""
        events = [sample_event_data for _ in range(5)]
        
        response = client.post(
            "/api/v1/biofouling/calculate",
            json={"events": events}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 5
    
    def test_fleet_summary(self, client):
        """Testa resumo da frota."""
        response = client.get("/api/v1/biofouling/fleet-summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_ships" in data
        assert "status_distribution" in data
        assert "level_distribution" in data


class TestAlertsEndpoints:
    """Testes dos endpoints de alertas."""
    
    def test_list_alerts(self, client):
        """Testa listagem de alertas."""
        response = client.get("/api/v1/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "alerts" in data
    
    def test_list_alerts_with_filters(self, client):
        """Testa listagem com filtros."""
        response = client.get("/api/v1/alerts?severity=critical&status=active")
        
        assert response.status_code == 200
    
    def test_get_alert_rules(self, client):
        """Testa listagem de regras."""
        response = client.get("/api/v1/alerts/rules")
        
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert len(data["rules"]) > 0


class TestAISEndpoints:
    """Testes dos endpoints AIS."""
    
    def test_ingest_ais_data(self, client, sample_ais_position_data):
        """Testa ingestão de dados AIS."""
        response = client.post(
            "/api/v1/ais/ingest",
            json={"positions": [sample_ais_position_data]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "accepted" in data
        assert "rejected" in data
        assert "processing_id" in data


class TestReportsEndpoints:
    """Testes dos endpoints de relatórios."""
    
    def test_generate_report(self, client):
        """Testa solicitação de geração de relatório."""
        request_data = {
            "type": "executive_summary",
            "period": {
                "start": (datetime.now() - timedelta(days=30)).date().isoformat(),
                "end": datetime.now().date().isoformat()
            },
            "format": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data
        assert "status" in data
