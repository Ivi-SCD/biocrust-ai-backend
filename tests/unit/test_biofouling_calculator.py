"""
Testes unitários para o calculador de bioincrustação.
"""

import pytest
from datetime import datetime, timedelta

from app.core.biofouling.calculator import BiofoulingCalculator


class TestBiofoulingCalculator:
    """Testes do calculador de bioincrustação."""
    
    @pytest.fixture
    def calculator(self):
        """Instância do calculador."""
        return BiofoulingCalculator()
    
    @pytest.fixture
    def sample_events(self):
        """Eventos de exemplo."""
        return [
            {
                "ship_name": "NAVIO A",
                "ship_class": "Aframax",
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 1, 2),
                "distance_nm": 280,
                "duration_hours": 24,
                "speed": 12.0,
                "displacement": 120000,
                "aft_draft": 14.5,
                "fwd_draft": 14.0,
                "mid_draft": 14.25,
                "trim": 0.5,
                "beaufort_scale": 3,
                "latitude": -23.5,
                "longitude": -45.0
            },
            {
                "ship_name": "NAVIO A",
                "ship_class": "Aframax",
                "start_date": datetime(2024, 6, 1),
                "end_date": datetime(2024, 6, 2),
                "distance_nm": 250,
                "duration_hours": 24,
                "speed": 10.5,
                "displacement": 125000,
                "aft_draft": 15.0,
                "fwd_draft": 14.5,
                "mid_draft": 14.75,
                "trim": 0.5,
                "beaufort_scale": 4,
                "latitude": -10.0,
                "longitude": -38.0
            }
        ]
    
    def test_calculator_initialization(self, calculator):
        """Testa inicialização do calculador."""
        assert calculator is not None
        assert calculator._model is not None
    
    def test_calculate_from_events_returns_results(self, calculator, sample_events):
        """Testa que cálculo retorna resultados."""
        results = calculator.calculate_from_events(sample_events)
        
        assert len(results) == len(sample_events)
        for result in results:
            assert "index" in result
            assert "normam_level" in result
            assert "status" in result
            assert "components" in result
    
    def test_index_value_range(self, calculator, sample_events):
        """Testa que índice está no range 0-100."""
        results = calculator.calculate_from_events(sample_events)
        
        for result in results:
            assert 0 <= result["index"] <= 100
    
    def test_normam_level_range(self, calculator, sample_events):
        """Testa que nível NORMAM está no range 0-4."""
        results = calculator.calculate_from_events(sample_events)
        
        for result in results:
            assert 0 <= result["normam_level"] <= 4
    
    def test_status_values(self, calculator, sample_events):
        """Testa valores de status."""
        results = calculator.calculate_from_events(sample_events)
        
        for result in results:
            assert result["status"] in ["ok", "warning", "critical"]
    
    def test_components_present(self, calculator, sample_events):
        """Testa que componentes estão presentes."""
        results = calculator.calculate_from_events(sample_events)
        
        for result in results:
            components = result["components"]
            assert "efficiency" in components
            assert "environmental" in components
            assert "temporal" in components
            assert "operational" in components
    
    def test_empty_events_list(self, calculator):
        """Testa com lista vazia de eventos."""
        results = calculator.calculate_from_events([])
        assert results == []
    
    def test_ship_length_override(self, calculator, sample_events):
        """Testa override de comprimento do navio."""
        results_default = calculator.calculate_from_events(sample_events)
        results_custom = calculator.calculate_from_events(sample_events, ship_length_m=300)
        
        # Resultados devem ser diferentes com comprimento diferente
        assert results_default[0]["index"] != results_custom[0]["index"] or \
               results_default[0]["components"] != results_custom[0]["components"]
    
    def test_get_status_ok(self, calculator):
        """Testa conversão de nível para status OK."""
        assert calculator._get_status(0) == "ok"
        assert calculator._get_status(1) == "ok"
    
    def test_get_status_warning(self, calculator):
        """Testa conversão de nível para status warning."""
        assert calculator._get_status(2) == "warning"
    
    def test_get_status_critical(self, calculator):
        """Testa conversão de nível para status critical."""
        assert calculator._get_status(3) == "critical"
        assert calculator._get_status(4) == "critical"
    
    def test_normam_level_description(self):
        """Testa descrições dos níveis NORMAM."""
        for level in range(5):
            desc = BiofoulingCalculator.get_normam_level_description(level)
            assert desc is not None
            assert len(desc) > 0
    
    def test_status_color(self):
        """Testa cores dos status."""
        assert BiofoulingCalculator.get_status_color("ok").startswith("#")
        assert BiofoulingCalculator.get_status_color("warning").startswith("#")
        assert BiofoulingCalculator.get_status_color("critical").startswith("#")


class TestBiofoulingPredictions:
    """Testes do previsor de bioincrustação."""
    
    @pytest.fixture
    def predictor(self):
        """Instância do previsor."""
        from app.core.biofouling.predictor import BiofoulingPredictor
        return BiofoulingPredictor()
    
    def test_predictor_initialization(self, predictor):
        """Testa inicialização do previsor."""
        assert predictor is not None
    
    def test_predict_returns_scenarios(self, predictor):
        """Testa que previsão retorna cenários."""
        result = predictor.predict(
            current_index=50,
            forecast_days=90
        )
        
        assert "scenarios" in result
        assert "recommendations" in result
        assert len(result["scenarios"]) > 0
    
    def test_predict_index_growth(self, predictor):
        """Testa que índice cresce com o tempo."""
        result = predictor.predict(
            current_index=50,
            forecast_days=90
        )
        
        scenario = result["scenarios"][0]
        predictions = scenario.predictions
        
        # Índice deve crescer
        first_index = predictions[0].index
        last_index = predictions[-1].index
        assert last_index > first_index
    
    def test_predict_index_saturation(self, predictor):
        """Testa que índice satura em 100."""
        result = predictor.predict(
            current_index=90,
            forecast_days=365
        )
        
        scenario = result["scenarios"][0]
        for prediction in scenario.predictions:
            assert prediction.index <= 100
    
    def test_predict_tropical_effect(self, predictor):
        """Testa efeito da exposição tropical."""
        result_low = predictor.predict(
            current_index=50,
            forecast_days=90,
            tropical_exposure_pct=0.2
        )
        
        result_high = predictor.predict(
            current_index=50,
            forecast_days=90,
            tropical_exposure_pct=0.8
        )
        
        # Maior exposição tropical = maior índice final
        low_final = result_low["scenarios"][0].predictions[-1].index
        high_final = result_high["scenarios"][0].predictions[-1].index
        assert high_final > low_final


class TestROICalculator:
    """Testes do calculador de ROI."""
    
    @pytest.fixture
    def roi_calculator(self):
        """Instância do calculador de ROI."""
        from app.core.biofouling.roi_calculator import ROICalculator
        return ROICalculator()
    
    def test_roi_calculator_initialization(self, roi_calculator):
        """Testa inicialização do calculador de ROI."""
        assert roi_calculator is not None
    
    def test_calculate_strategies_returns_result(self, roi_calculator):
        """Testa que cálculo retorna resultado."""
        strategies = [
            {
                "name": "clean_now",
                "cleaning_date": datetime.now().date(),
                "cleaning_cost_brl": 85000
            }
        ]
        
        result = roi_calculator.calculate_strategies(
            current_index=67,
            strategies=strategies
        )
        
        assert "analyzed_strategies" in result
        assert "recommendation" in result
        assert len(result["analyzed_strategies"]) == 1
    
    def test_clean_now_vs_later_roi(self, roi_calculator):
        """Testa que limpar agora tem melhor ROI que limpar depois."""
        from datetime import date, timedelta
        
        strategies = [
            {
                "name": "clean_now",
                "cleaning_date": date.today(),
                "cleaning_cost_brl": 85000
            },
            {
                "name": "clean_in_30_days",
                "cleaning_date": date.today() + timedelta(days=30),
                "cleaning_cost_brl": 85000
            }
        ]
        
        result = roi_calculator.calculate_strategies(
            current_index=67,
            strategies=strategies
        )
        
        clean_now = next(s for s in result["analyzed_strategies"] if s.name == "clean_now")
        clean_later = next(s for s in result["analyzed_strategies"] if s.name == "clean_in_30_days")
        
        # Limpar agora deve ter ROI melhor ou custo total menor
        assert clean_now.roi_percentage >= clean_later.roi_percentage or \
               clean_now.costs.total_cost <= clean_later.costs.total_cost
