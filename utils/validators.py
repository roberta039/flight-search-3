"""
Funcții de validare pentru input-uri
"""
from datetime import datetime, date
from typing import Tuple, Optional
import re


def validate_iata_code(code: str) -> Tuple[bool, str]:
    """
    Validează un cod IATA de aeroport
    
    Args:
        code: Codul de verificat
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not code:
        return False, "Airport code is required"
    
    code = code.strip().upper()
    
    if len(code) != 3:
        return False, "IATA code must be exactly 3 characters"
    
    if not code.isalpha():
        return False, "IATA code must contain only letters"
    
    return True, ""


def validate_date(
    date_str: str, 
    min_date: Optional[date] = None,
    max_date: Optional[date] = None
) -> Tuple[bool, str, Optional[date]]:
    """
    Validează o dată
    
    Args:
        date_str: Data ca string
        min_date: Data minimă permisă
        max_date: Data maximă permisă
    
    Returns:
        Tuple (is_valid, error_message, parsed_date)
    """
    if not date_str:
        return False, "Date is required", None
    
    try:
        if isinstance(date_str, date):
            parsed = date_str
        elif isinstance(date_str, datetime):
            parsed = date_str.date()
        else:
            parsed = datetime.strptime(str(date_str), '%Y-%m-%d').date()
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD", None
    
    if min_date and parsed < min_date:
        return False, f"Date must be on or after {min_date}", None
    
    if max_date and parsed > max_date:
        return False, f"Date must be on or before {max_date}", None
    
    return True, "", parsed


def validate_passengers(
    adults: int, 
    children: int = 0, 
    infants: int = 0
) -> Tuple[bool, str]:
    """
    Validează numărul de pasageri
    
    Args:
        adults: Număr adulți
        children: Număr copii
        infants: Număr bebeluși
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if adults < 1:
        return False, "At least 1 adult is required"
    
    if adults > 9:
        return False, "Maximum 9 adults allowed"
    
    if children < 0:
        return False, "Number of children cannot be negative"
    
    if infants < 0:
        return False, "Number of infants cannot be negative"
    
    if infants > adults:
        return False, "Number of infants cannot exceed number of adults"
    
    total = adults + children + infants
    if total > 9:
        return False, "Maximum 9 passengers allowed per booking"
    
    return True, ""


def validate_search_params(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0
) -> Tuple[bool, list]:
    """
    Validează toți parametrii de căutare
    
    Args:
        origin: Codul aeroportului de plecare
        destination: Codul aeroportului de sosire
        departure_date: Data plecării
        return_date: Data întoarcerii (opțional)
        adults: Număr adulți
        children: Număr copii
        infants: Număr bebeluși
    
    Returns:
        Tuple (is_valid, list_of_errors)
    """
    errors = []
    today = date.today()
    max_date = date(today.year + 1, today.month, today.day)
    
    # Validare origine
    is_valid, error = validate_iata_code(origin)
    if not is_valid:
        errors.append(f"Origin: {error}")
    
    # Validare destinație
    is_valid, error = validate_iata_code(destination)
    if not is_valid:
        errors.append(f"Destination: {error}")
    
    # Verifică că origine și destinație sunt diferite
    if origin and destination and origin.upper() == destination.upper():
        errors.append("Origin and destination must be different")
    
    # Validare data plecare
    is_valid, error, dep_date = validate_date(departure_date, min_date=today, max_date=max_date)
    if not is_valid:
        errors.append(f"Departure date: {error}")
    
    # Validare data întoarcere
    if return_date:
        is_valid, error, ret_date = validate_date(return_date, min_date=today, max_date=max_date)
        if not is_valid:
            errors.append(f"Return date: {error}")
        elif dep_date and ret_date and ret_date < dep_date:
            errors.append("Return date must be after departure date")
    
    # Validare pasageri
    is_valid, error = validate_passengers(adults, children, infants)
    if not is_valid:
        errors.append(f"Passengers: {error}")
    
    return len(errors) == 0, errors


def sanitize_input(text: str) -> str:
    """
    Curăță input-ul de caractere potențial periculoase
    
    Args:
        text: Textul de curățat
    
    Returns:
        Textul curățat
    """
    if not text:
        return ""
    
    # Elimină caractere speciale
    text = re.sub(r'[<>"\';(){}]', '', text)
    
    # Trimează whitespace
    text = text.strip()
    
    return text
