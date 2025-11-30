"""
Integração com o modelo de bioincrustação existente.

Este módulo integra a classe ModeloBioincrustacaoFisico do arquivo
modelo_bioincrustacao_fisico.py, fornecendo uma interface limpa para uso na API.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import structlog

# Adicionar diretório do modelo ao path se necessário
MODEL_PATH = Path(__file__).parent.parent.parent.parent.parent / "modelo_bioincrustacao_fisico.py"
ETL_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / "etl"

if str(ETL_PATH) not in sys.path:
    sys.path.insert(0, str(ETL_PATH))

# Importar o modelo existente
from modelo_bioincrustacao_fisico import ModeloBioincrustacaoFisico

logger = structlog.get_logger()


class BiofoulingCalculator:
    """
    Calculador de índice de bioincrustação.
    
    Encapsula o modelo físico-estatístico existente (ModeloBioincrustacaoFisico)
    e fornece interface limpa para uso na API.
    
    O modelo não requer treinamento de ML - usa princípios físicos conhecidos
    da indústria naval para estimar bioincrustação.
    """
    
    def __init__(self):
        """Inicializa o calculador com o modelo existente."""
        self._model = ModeloBioincrustacaoFisico()
        logger.info("biofouling_calculator_initialized")
    
    def calculate_from_events(
        self,
        events: List[Dict[str, Any]],
        ship_length_m: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula índice de bioincrustação para uma lista de eventos.
        
        Args:
            events: Lista de eventos de navegação
            ship_length_m: Comprimento do navio em metros (opcional)
            
        Returns:
            Lista de resultados com índices calculados
        """
        if not events:
            return []
        
        # Converter eventos para DataFrame no formato esperado pelo modelo
        df = self._events_to_dataframe(events)
        
        logger.info(
            "calculating_biofouling_index",
            num_events=len(events),
            ship_length=ship_length_m
        )
        
        # Executar cálculo usando o modelo existente
        try:
            result_df = self._model.calcular_indice_bioincrustacao(
                df,
                comprimento_navio=ship_length_m
            )
            
            # Converter resultado para lista de dicionários
            results = self._dataframe_to_results(result_df, events)
            
            logger.info(
                "biofouling_calculation_complete",
                num_results=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "biofouling_calculation_error",
                error=str(e)
            )
            raise
    
    def _events_to_dataframe(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Converte lista de eventos para DataFrame no formato do modelo.
        
        Args:
            events: Lista de eventos
            
        Returns:
            DataFrame formatado
        """
        # Mapear campos do schema para colunas do modelo
        rows = []
        for event in events:
            row = {
                "sessionId": event.get("session_id", 0),
                "shipName": event.get("ship_name"),
                "class": event.get("ship_class", "Aframax"),
                "startGMTDate": pd.to_datetime(event.get("start_date")),
                "endGMTDate": pd.to_datetime(event.get("end_date")),
                "duration": event.get("duration_hours", 24),
                "distance": event.get("distance_nm", 0),
                "speed": event.get("speed", 0),
                "speedGps": event.get("speed", 0),
                "displacement": event.get("displacement", 120000),
                "aftDraft": event.get("aft_draft", 14),
                "fwdDraft": event.get("fwd_draft", 14),
                "midDraft": event.get("mid_draft", 14),
                "TRIM": event.get("trim", 0.5),
                "beaufortScale": event.get("beaufort_scale", 3),
                "decLatitude": event.get("latitude", -23),
                "decLongitude": event.get("longitude", -45),
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _dataframe_to_results(
        self,
        df: pd.DataFrame,
        original_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Converte DataFrame de resultado para lista de dicionários.
        
        Args:
            df: DataFrame com resultados
            original_events: Eventos originais para referência
            
        Returns:
            Lista de resultados formatados
        """
        results = []
        
        for idx, row in df.iterrows():
            # Extrair índice e componentes
            index_value = float(row.get("indice_bioincrustacao", 0))
            normam_level = int(row.get("nivel_normam_estimado", 0))
            status = self._get_status(normam_level)
            
            result = {
                "event_index": idx,
                "ship_name": row.get("shipName", ""),
                "index": round(index_value, 1),
                "normam_level": normam_level,
                "status": status,
                "components": {
                    "efficiency": round(float(row.get("comp_eficiencia", 0)), 1),
                    "environmental": round(float(row.get("comp_ambiental", 0)), 1),
                    "temporal": round(float(row.get("comp_temporal", 0)), 1),
                    "operational": round(float(row.get("comp_operacional", 0)), 1),
                },
                "calculated_at": datetime.utcnow().isoformat()
            }
            
            # Adicionar métricas de eficiência se disponíveis
            if idx < len(original_events):
                event = original_events[idx]
                if event.get("distance_nm") and event.get("displacement"):
                    nm_per_ton = event["distance_nm"] / (event["displacement"] / 1000)
                    baseline = 6.0  # baseline estimado
                    degradation = max(0, (baseline - nm_per_ton) / baseline * 100)
                    
                    result["efficiency_metrics"] = {
                        "nm_per_ton": round(nm_per_ton, 2),
                        "baseline_nm_per_ton": baseline,
                        "degradation_pct": round(degradation, 1)
                    }
            
            results.append(result)
        
        return results
    
    def _get_status(self, normam_level: int) -> str:
        """
        Converte nível NORMAM para status de alerta.
        
        Args:
            normam_level: Nível NORMAM (0-4)
            
        Returns:
            Status: 'ok', 'warning' ou 'critical'
        """
        if normam_level <= 1:
            return "ok"
        elif normam_level == 2:
            return "warning"
        else:
            return "critical"
    
    def generate_report(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Gera relatório executivo usando o modelo existente.
        
        Args:
            df: DataFrame com índices calculados
            
        Returns:
            Relatório estruturado
        """
        return self._model.gerar_relatorio(df)
    
    @staticmethod
    def get_normam_level_description(level: int) -> str:
        """
        Retorna descrição do nível NORMAM.
        
        Args:
            level: Nível NORMAM (0-4)
            
        Returns:
            Descrição do nível
        """
        descriptions = {
            0: "Limpo - Sem bioincrustação visível",
            1: "Microincrustação - Biofilme/limo, impacto mínimo",
            2: "Macroincrustação leve - 1-15% de cobertura",
            3: "Macroincrustação moderada - 16-40% de cobertura",
            4: "Macroincrustação pesada - >40% de cobertura",
        }
        return descriptions.get(level, "Nível desconhecido")
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """
        Retorna cor associada ao status.
        
        Args:
            status: Status ('ok', 'warning', 'critical')
            
        Returns:
            Cor em hexadecimal
        """
        colors = {
            "ok": "#22c55e",      # Verde
            "warning": "#f59e0b", # Amarelo/Laranja
            "critical": "#ef4444" # Vermelho
        }
        return colors.get(status, "#6b7280")
