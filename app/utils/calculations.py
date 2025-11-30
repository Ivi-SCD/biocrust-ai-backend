"""
Funções utilitárias de cálculo.
"""

import math
from typing import Tuple


def classify_water_type(latitude: float) -> str:
    """
    Classifica tipo de água baseado na latitude.
    
    Args:
        latitude: Latitude em graus decimais
        
    Returns:
        str: 'tropical', 'subtropical' ou 'temperate'
    """
    abs_lat = abs(latitude)
    if abs_lat < 20:
        return "tropical"
    elif abs_lat < 35:
        return "subtropical"
    else:
        return "temperate"


def calculate_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calcula distância entre dois pontos usando fórmula de Haversine.
    
    Args:
        lat1: Latitude do ponto 1
        lon1: Longitude do ponto 1
        lat2: Latitude do ponto 2
        lon2: Longitude do ponto 2
        
    Returns:
        float: Distância em milhas náuticas
    """
    # Converter para radianos
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Diferenças
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Raio da Terra em milhas náuticas
    r = 3440.065
    
    return c * r


def get_alert_status(normam_level: int) -> str:
    """
    Converte nível NORMAM para status de alerta.
    
    Args:
        normam_level: Nível NORMAM (0-4)
        
    Returns:
        str: 'ok', 'warning' ou 'critical'
    """
    if normam_level <= 1:
        return "ok"
    elif normam_level == 2:
        return "warning"
    else:
        return "critical"


def calculate_fuel_impact(
    index: float,
    baseline_consumption: float = 50.0
) -> Tuple[float, float]:
    """
    Calcula impacto do índice no consumo de combustível.
    
    Args:
        index: Índice de bioincrustação (0-100)
        baseline_consumption: Consumo base em toneladas/dia
        
    Returns:
        Tuple com (consumo adicional %, consumo adicional em toneladas)
    """
    # Cada 10 pontos de índice = ~3% mais consumo
    # Assumindo índice 20 como baseline (navio limpo)
    additional_pct = max(0, (index - 20) * 0.003)
    additional_tons = baseline_consumption * additional_pct
    
    return additional_pct * 100, additional_tons


def predict_future_index(
    current_index: float,
    days_ahead: int,
    tropical_exposure_pct: float = 0.5
) -> float:
    """
    Prevê índice futuro usando modelo de crescimento.
    
    Args:
        current_index: Índice atual
        days_ahead: Dias no futuro
        tropical_exposure_pct: Percentual de exposição tropical
        
    Returns:
        float: Índice previsto
    """
    if days_ahead <= 0:
        return current_index
    
    # Taxa base de crescimento (índice/mês)
    base_rate = 8.0
    
    # Fator de aceleração em águas tropicais
    tropical_factor = 1 + (tropical_exposure_pct * 1.5)
    
    # Curva logarítmica
    months = days_ahead / 30
    growth = base_rate * tropical_factor * math.log1p(months)
    
    # Saturar em 100
    return min(100, current_index + growth)
