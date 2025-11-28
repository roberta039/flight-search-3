"""
Servicii pentru căutarea zborurilor folosind API-uri gratuite
- Sky-Scrapper (Skyscanner via RapidAPI)
- Kiwi Tequila API
- AirLabs (pentru aeroporturi)
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import streamlit as st

from config.settings import Settings
from .cache_manager import cache_manager


# ============================================
# DICȚIONARE ȚĂRI ȘI CONTINENTE
# ============================================

COUNTRY_NAMES = {
    # Europa
    "AD": "Andorra", "AL": "Albania", "AT": "Austria", "BA": "Bosnia și Herțegovina",
    "BE": "Belgia", "BG": "Bulgaria", "BY": "Belarus", "CH": "Elveția",
    "CY": "Cipru", "CZ": "Cehia", "DE": "Germania", "DK": "Danemarca",
    "EE": "Estonia", "ES": "Spania", "FI": "Finlanda", "FO": "Insulele Feroe",
    "FR": "Franța", "GB": "Marea Britanie", "GI": "Gibraltar", "GR": "Grecia",
    "HR": "Croația", "HU": "Ungaria", "IE": "Irlanda", "IS": "Islanda",
    "IT": "Italia", "LI": "Liechtenstein", "LT": "Lituania", "LU": "Luxemburg",
    "LV": "Letonia", "MC": "Monaco", "MD": "Moldova", "ME": "Muntenegru",
    "MK": "Macedonia de Nord", "MT": "Malta", "NL": "Olanda", "NO": "Norvegia",
    "PL": "Polonia", "PT": "Portugalia", "RO": "România", "RS": "Serbia",
    "RU": "Rusia", "SE": "Suedia", "SI": "Slovenia", "SK": "Slovacia",
    "SM": "San Marino", "UA": "Ucraina", "VA": "Vatican", "XK": "Kosovo",
    # Asia
    "AE": "Emiratele Arabe Unite", "AF": "Afganistan", "AM": "Armenia",
    "AZ": "Azerbaidjan", "BD": "Bangladesh", "BH": "Bahrain", "BN": "Brunei",
    "BT": "Bhutan", "CN": "China", "GE": "Georgia", "HK": "Hong Kong",
    "ID": "Indonezia", "IL": "Israel", "IN": "India", "IQ": "Irak",
    "IR": "Iran", "JO": "Iordania", "JP": "Japonia", "KG": "Kârgâzstan",
    "KH": "Cambodgia", "KP": "Coreea de Nord", "KR": "Coreea de Sud",
    "KW": "Kuweit", "KZ": "Kazahstan", "LA": "Laos", "LB": "Liban",
    "LK": "Sri Lanka", "MM": "Myanmar", "MN": "Mongolia", "MO": "Macao",
    "MV": "Maldive", "MY": "Malaezia", "NP": "Nepal", "OM": "Oman",
    "PH": "Filipine", "PK": "Pakistan", "PS": "Palestina", "QA": "Qatar",
    "SA": "Arabia Saudită", "SG": "Singapore", "SY": "Siria", "TH": "Thailanda",
    "TJ": "Tadjikistan", "TL": "Timorul de Est", "TM": "Turkmenistan",
    "TR": "Turcia", "TW": "Taiwan", "UZ": "Uzbekistan", "VN": "Vietnam",
    "YE": "Yemen",
    # Africa
    "AO": "Angola", "BF": "Burkina Faso", "BI": "Burundi", "BJ": "Benin",
    "BW": "Botswana", "CD": "Congo (RD)", "CF": "Republica Centrafricană",
    "CG": "Congo", "CI": "Coasta de Fildeș", "CM": "Camerun", "CV": "Capul Verde",
    "DJ": "Djibouti", "DZ": "Algeria", "EG": "Egipt", "EH": "Sahara Occidentală",
    "ER": "Eritreea", "ET": "Etiopia", "GA": "Gabon", "GH": "Ghana",
    "GM": "Gambia", "GN": "Guineea", "GQ": "Guineea Ecuatorială",
    "GW": "Guineea-Bissau", "KE": "Kenya", "KM": "Comore", "LR": "Liberia",
    "LS": "Lesotho", "LY": "Libia", "MA": "Maroc", "MG": "Madagascar",
    "ML": "Mali", "MR": "Mauritania", "MU": "Mauritius", "MW": "Malawi",
    "MZ": "Mozambic", "NA": "Namibia", "NE": "Niger", "NG": "Nigeria",
    "RE": "Réunion", "RW": "Rwanda", "SC": "Seychelles", "SD": "Sudan",
    "SL": "Sierra Leone", "SN": "Senegal", "SO": "Somalia", "SS": "Sudanul de Sud",
    "ST": "São Tomé și Príncipe", "SZ": "Eswatini", "TD": "Ciad", "TG": "Togo",
    "TN": "Tunisia", "TZ": "Tanzania", "UG": "Uganda", "YT": "Mayotte",
    "ZA": "Africa de Sud", "ZM": "Zambia", "ZW": "Zimbabwe",
    # America de Nord
    "AG": "Antigua și Barbuda", "AI": "Anguilla", "AW": "Aruba", "BB": "Barbados",
    "BM": "Bermuda", "BS": "Bahamas", "BZ": "Belize", "CA": "Canada",
    "CR": "Costa Rica", "CU": "Cuba", "CW": "Curaçao", "DM": "Dominica",
    "DO": "Republica Dominicană", "GD": "Grenada", "GL": "Groenlanda",
    "GP": "Guadelupa", "GT": "Guatemala", "HN": "Honduras", "HT": "Haiti",
    "JM": "Jamaica", "KN": "Saint Kitts și Nevis", "KY": "Insulele Cayman",
    "LC": "Saint Lucia", "MQ": "Martinica", "MS": "Montserrat", "MX": "Mexic",
    "NI": "Nicaragua", "PA": "Panama", "PM": "Saint Pierre și Miquelon",
    "PR": "Puerto Rico", "SV": "El Salvador", "SX": "Sint Maarten",
    "TC": "Insulele Turks și Caicos", "TT": "Trinidad și Tobago",
    "US": "Statele Unite", "VC": "Saint Vincent și Grenadine",
    "VG": "Insulele Virgine Britanice", "VI": "Insulele Virgine Americane",
    # America de Sud
    "AR": "Argentina", "BO": "Bolivia", "BR": "Brazilia", "CL": "Chile",
    "CO": "Columbia", "EC": "Ecuador", "FK": "Insulele Falkland",
    "GF": "Guyana Franceză", "GY": "Guyana", "PE": "Peru", "PY": "Paraguay",
    "SR": "Surinam", "UY": "Uruguay", "VE": "Venezuela",
    # Oceania
    "AS": "Samoa Americană", "AU": "Australia", "CK": "Insulele Cook",
    "FJ": "Fiji", "FM": "Micronezia", "GU": "Guam", "KI": "Kiribati",
    "MH": "Insulele Marshall", "NC": "Noua Caledonie", "NF": "Insula Norfolk",
    "NR": "Nauru", "NU": "Niue", "NZ": "Noua Zeelandă", "PF": "Polinezia Franceză",
    "PG": "Papua Noua Guinee", "PN": "Insulele Pitcairn", "PW": "Palau",
    "SB": "Insulele Solomon", "TO": "Tonga", "TV": "Tuvalu", "VU": "Vanuatu",
    "WF": "Wallis și Futuna", "WS": "Samoa",
}

CONTINENT_MAPPING = {
    # Europa
    "AD": "EU", "AL": "EU", "AT": "EU", "BA": "EU", "BE": "EU", "BG": "EU",
    "BY": "EU", "CH": "EU", "CY": "EU", "CZ": "EU", "DE": "EU", "DK": "EU",
    "EE": "EU", "ES": "EU", "FI": "EU", "FO": "EU", "FR": "EU", "GB": "EU",
    "GI": "EU", "GR": "EU", "HR": "EU", "HU": "EU", "IE": "EU", "IS": "EU",
    "IT": "EU", "LI": "EU", "LT": "EU", "LU": "EU", "LV": "EU", "MC": "EU",
    "MD": "EU", "ME": "EU", "MK": "EU", "MT": "EU", "NL": "EU", "NO": "EU",
    "PL": "EU", "PT": "EU", "RO": "EU", "RS": "EU", "RU": "EU", "SE": "EU",
    "SI": "EU", "SK": "EU", "SM": "EU", "UA": "EU", "VA": "EU", "XK": "EU",
    # Asia
    "AE": "AS", "AF": "AS", "AM": "AS", "AZ": "AS", "BD": "AS", "BH": "AS",
    "BN": "AS", "BT": "AS", "CN": "AS", "GE": "AS", "HK": "AS", "ID": "AS",
    "IL": "AS", "IN": "AS", "IQ": "AS", "IR": "AS", "JO": "AS", "JP": "AS",
    "KG": "AS", "KH": "AS", "KP": "AS", "KR": "AS", "KW": "AS", "KZ": "AS",
    "LA": "AS", "LB": "AS", "LK": "AS", "MM": "AS", "MN": "AS", "MO": "AS",
    "MV": "AS", "MY": "AS", "NP": "AS", "OM": "AS", "PH": "AS", "PK": "AS",
    "PS": "AS", "QA": "AS", "SA": "AS", "SG": "AS", "SY": "AS", "TH": "AS",
    "TJ": "AS", "TL": "AS", "TM": "AS", "TR": "AS", "TW": "AS", "UZ": "AS",
    "VN": "AS", "YE": "AS",
    # Africa
    "AO": "AF", "BF": "AF", "BI": "AF", "BJ": "AF", "BW": "AF", "CD": "AF",
    "CF": "AF", "CG": "AF", "CI": "AF", "CM": "AF", "CV": "AF", "DJ": "AF",
    "DZ": "AF", "EG": "AF", "EH": "AF", "ER": "AF", "ET": "AF", "GA": "AF",
    "GH": "AF", "GM": "AF", "GN": "AF", "GQ": "AF", "GW": "AF", "KE": "AF",
    "KM": "AF", "LR": "AF", "LS": "AF", "LY": "AF", "MA": "AF", "MG": "AF",
    "ML": "AF", "MR": "AF", "MU": "AF", "MW": "AF", "MZ": "AF", "NA": "AF",
    "NE": "AF", "NG": "AF", "RE": "AF", "RW": "AF", "SC": "AF", "SD": "AF",
    "SL": "AF", "SN": "AF", "SO": "AF", "SS": "AF", "ST": "AF", "SZ": "AF",
    "TD": "AF", "TG": "AF", "TN": "AF", "TZ": "AF", "UG": "AF", "YT": "AF",
    "ZA": "AF", "ZM": "AF", "ZW": "AF",
    # America de Nord
    "AG": "NA", "AI": "NA", "AW": "NA", "BB": "NA", "BM": "NA", "BS": "NA",
    "BZ": "NA", "CA": "NA", "CR": "NA", "CU": "NA", "CW": "NA", "DM": "NA",
    "DO": "NA", "GD": "NA", "GL": "NA", "GP": "NA", "GT": "NA", "HN": "NA",
    "HT": "NA", "JM": "NA", "KN": "NA", "KY": "NA", "LC": "NA", "MQ": "NA",
    "MS": "NA", "MX": "NA", "NI": "NA", "PA": "NA", "PM": "NA", "PR": "NA",
    "SV": "NA", "SX": "NA", "TC": "NA", "TT": "NA", "US": "NA", "VC": "NA",
    "VG": "NA", "VI": "NA",
    # America de Sud
    "AR": "SA", "BO": "SA", "BR": "SA", "CL": "SA", "CO": "SA", "EC": "SA",
    "FK": "SA", "GF": "SA", "GY": "SA", "PE": "SA", "PY": "SA", "SR": "SA",
    "UY": "SA", "VE": "SA",
    # Oceania
    "AS": "OC", "AU": "OC", "CK": "OC", "FJ": "OC", "FM": "OC", "GU": "OC",
    "KI": "OC", "MH": "OC", "NC": "OC", "NF": "OC", "NR": "OC", "NU": "OC",
    "NZ": "OC", "PF": "OC", "PG": "OC", "PN": "OC", "PW": "OC", "SB": "OC",
    "TO": "OC", "TV": "OC", "VU": "OC", "WF": "OC", "WS": "OC",
}

CONTINENT_NAMES = {
    "AF": "Africa",
    "AS": "Asia",
    "EU": "Europa",
    "NA": "America de Nord",
    "OC": "Oceania",
    "SA": "America de Sud"
}


def get_country_name(country_code: str) -> str:
    return COUNTRY_NAMES.get(country_code.upper(), country_code)


def get_continent_code(country_code: str) -> str:
    return CONTINENT_MAPPING.get(country_code.upper(), "EU")


def get_continent_name(continent_code: str) -> str:
    return CONTINENT_NAMES.get(continent_code.upper(), continent_code)


# ============================================
# MODELE DE DATE
# ============================================

@dataclass
class FlightOffer:
    """Reprezintă o ofertă de zbor"""
    id: str
    source: str
    airline: str
    airline_code: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    price: float
    currency: str
    cabin_class: str
    stops: int
    segments: List[dict]
    booking_link: Optional[str] = None
    seats_available: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'ID': self.id,
            'Sursă': self.source,
            'Companie': self.airline,
            'Cod': self.airline_code,
            'De la': self.origin,
            'Către': self.destination,
            'Plecare': self.departure_time.strftime('%Y-%m-%d %H:%M'),
            'Sosire': self.arrival_time.strftime('%Y-%m-%d %H:%M'),
            'Durată': self.duration,
            'Preț': self.price,
            'Monedă': self.currency,
            'Clasă': self.cabin_class,
            'Escale': self.stops,
            'Locuri': self.seats_available or 'N/A',
            'Link': self.booking_link or ''
        }


class APIError(Exception):
    def __init__(self, message: str, status_code: int = None, api_name: str = None):
        self.message = message
        self.status_code = status_code
        self.api_name = api_name
        super().__init__(self.message)


# ============================================
# 
