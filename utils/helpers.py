"""
Funcții helper pentru aplicație
"""
from datetime import datetime, timedelta
from typing import Optional
import re


def format_duration(duration_str: str) -> str:
    """
    Formatează durata zborului
    
    Args:
        duration_str: Durata în format ISO 8601 (PT2H30M) sau alte formate
    
    Returns:
        String formatat (ex: "2h 30m")
    """
    if not duration_str:
        return "N/A"
    
    # Dacă e deja formatat
    if 'h' in duration_str.lower() and 'm' not in duration_str.lower():
        return duration_str
    
    # Parse ISO 8601 duration
    if duration_str.startswith('PT'):
        hours = 0
        minutes = 0
        
        h_match = re.search(r'(\d+)H', duration_str)
        m_match = re.search(r'(\d+)M', duration_str)
        
        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))
        
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        elif minutes:
            return f"{minutes}m"
    
    return duration_str


def format_price(price: float, currency: str = 'EUR') -> str:
    """
    Formatează prețul
    
    Args:
        price: Prețul numeric
        currency: Codul monedei
    
    Returns:
        String formatat (ex: "€123.45")
    """
    currency_symbols = {
        'EUR': '€',
        'USD': '$',
        'GBP': '£',
        'RON': 'lei',
        'CHF': 'CHF'
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency in ['EUR', 'USD', 'GBP']:
        return f"{symbol}{price:,.2f}"
    else:
        return f"{price:,.2f} {symbol}"


def get_airline_logo(airline_code: str, size: int = 32) -> str:
    """
    Returnează URL-ul logo-ului companiei aeriene
    
    Args:
        airline_code: Codul IATA al companiei
        size: Dimensiunea logo-ului
    
    Returns:
        URL-ul logo-ului
    """
    # Folosim un serviciu public pentru logo-uri
    return f"https://images.kiwi.com/airlines/64/{airline_code}.png"


def calculate_flight_duration(departure: datetime, arrival: datetime) -> str:
    """
    Calculează durata zborului
    
    Args:
        departure: Data/ora plecării
        arrival: Data/ora sosirii
    
    Returns:
        Durata formatată
    """
    duration = arrival - departure
    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes = remainder // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def get_time_of_day(dt: datetime) -> str:
    """
    Returnează perioada zilei
    
    Args:
        dt: Datetime object
    
    Returns:
        Descrierea perioadei (Morning, Afternoon, Evening, Night)
    """
    hour = dt.hour
    
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parsează o dată din diverse formate
    
    Args:
        date_str: String cu data
    
    Returns:
        Datetime object sau None
    """
    formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d.%m.%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def get_date_range(start_date: datetime, days: int = 7) -> list:
    """
    Generează o listă de date
    
    Args:
        start_date: Data de start
        days: Numărul de zile
    
    Returns:
        Lista de date
    """
    return [start_date + timedelta(days=i) for i in range(days)]


def format_datetime_for_display(dt: datetime) -> str:
    """
    Formatează datetime pentru afișare
    
    Args:
        dt: Datetime object
    
    Returns:
        String formatat
    """
    return dt.strftime('%a, %d %b %Y %H:%M')


def get_stops_description(stops: int) -> str:
    """
    Returnează descrierea numărului de escale
    
    Args:
        stops: Numărul de escale
    
    Returns:
        Descrierea (Direct, 1 stop, 2+ stops)
    """
    if stops == 0:
        return "Direct"
    elif stops == 1:
        return "1 stop"
    else:
        return f"{stops} stops"


def calculate_price_per_person(total_price: float, passengers: int) -> float:
    """
    Calculează prețul per persoană
    
    Args:
        total_price: Prețul total
        passengers: Numărul de pasageri
    
    Returns:
        Prețul per persoană
    """
    if passengers <= 0:
        return total_price
    return round(total_price / passengers, 2)
