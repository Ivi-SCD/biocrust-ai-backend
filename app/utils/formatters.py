"""
Funções de formatação.
"""

from datetime import datetime
from typing import Optional


def format_currency(value: float, currency: str = "BRL") -> str:
    """
    Formata valor monetário.
    
    Args:
        value: Valor numérico
        currency: Código da moeda
        
    Returns:
        str: Valor formatado
    """
    if currency == "BRL":
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif currency == "USD":
        return f"$ {value:,.2f}"
    else:
        return f"{value:,.2f} {currency}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Formata valor percentual.
    
    Args:
        value: Valor (0-100 ou 0-1)
        decimals: Casas decimais
        
    Returns:
        str: Valor formatado com %
    """
    # Se valor <= 1, assume que está em formato decimal
    if value <= 1:
        value = value * 100
    
    return f"{value:.{decimals}f}%"


def format_datetime(
    dt: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Formata datetime.
    
    Args:
        dt: Objeto datetime
        format_str: String de formato
        
    Returns:
        str: Data formatada
    """
    return dt.strftime(format_str)


def format_duration(hours: float) -> str:
    """
    Formata duração em horas para string legível.
    
    Args:
        hours: Duração em horas
        
    Returns:
        str: Duração formatada
    """
    if hours < 1:
        return f"{int(hours * 60)} minutos"
    elif hours < 24:
        return f"{hours:.1f} horas"
    else:
        days = hours / 24
        if days < 30:
            return f"{days:.1f} dias"
        else:
            months = days / 30
            return f"{months:.1f} meses"


def format_distance(nm: float) -> str:
    """
    Formata distância em milhas náuticas.
    
    Args:
        nm: Distância em milhas náuticas
        
    Returns:
        str: Distância formatada
    """
    if nm < 1:
        return f"{nm:.2f} nm"
    elif nm < 100:
        return f"{nm:.1f} nm"
    else:
        return f"{nm:,.0f} nm"
