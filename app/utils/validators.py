"""
Funções de validação customizadas.
"""

from datetime import datetime, date
from typing import Optional, Tuple


def validate_coordinates(
    latitude: float,
    longitude: float
) -> Tuple[bool, Optional[str]]:
    """
    Valida coordenadas geográficas.
    
    Args:
        latitude: Latitude em graus decimais
        longitude: Longitude em graus decimais
        
    Returns:
        Tuple (válido, mensagem de erro)
    """
    if not -90 <= latitude <= 90:
        return False, f"Latitude {latitude} fora do range [-90, 90]"
    
    if not -180 <= longitude <= 180:
        return False, f"Longitude {longitude} fora do range [-180, 180]"
    
    return True, None


def validate_date_range(
    start_date: datetime,
    end_date: datetime
) -> Tuple[bool, Optional[str]]:
    """
    Valida range de datas.
    
    Args:
        start_date: Data inicial
        end_date: Data final
        
    Returns:
        Tuple (válido, mensagem de erro)
    """
    if start_date > end_date:
        return False, "Data inicial não pode ser maior que data final"
    
    # Limitar range a 2 anos
    max_range_days = 365 * 2
    if (end_date - start_date).days > max_range_days:
        return False, f"Range não pode exceder {max_range_days} dias"
    
    return True, None


def validate_normam_level(level: int) -> Tuple[bool, Optional[str]]:
    """
    Valida nível NORMAM.
    
    Args:
        level: Nível NORMAM
        
    Returns:
        Tuple (válido, mensagem de erro)
    """
    if not 0 <= level <= 4:
        return False, f"Nível NORMAM {level} fora do range [0, 4]"
    
    return True, None


def validate_index_value(index: float) -> Tuple[bool, Optional[str]]:
    """
    Valida valor de índice de bioincrustação.
    
    Args:
        index: Valor do índice
        
    Returns:
        Tuple (válido, mensagem de erro)
    """
    if not 0 <= index <= 100:
        return False, f"Índice {index} fora do range [0, 100]"
    
    return True, None


def validate_beaufort_scale(scale: int) -> Tuple[bool, Optional[str]]:
    """
    Valida escala Beaufort.
    
    Args:
        scale: Valor na escala Beaufort
        
    Returns:
        Tuple (válido, mensagem de erro)
    """
    if not 0 <= scale <= 12:
        return False, f"Escala Beaufort {scale} fora do range [0, 12]"
    
    return True, None


def validate_ship_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Valida nome de navio.
    
    Args:
        name: Nome do navio
        
    Returns:
        Tuple (válido, mensagem de erro)
    """
    if not name or len(name.strip()) == 0:
        return False, "Nome do navio não pode ser vazio"
    
    if len(name) > 100:
        return False, "Nome do navio não pode exceder 100 caracteres"
    
    return True, None
