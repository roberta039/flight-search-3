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
# SKY-SCRAPPER API (Skyscanner via RapidAPI)
# ============================================

class SkyScrapperAPI:
    """Client pentru Sky-Scrapper API (Skyscanner data via RapidAPI)"""
    
    def __init__(self):
        keys = Settings.get_api_keys()
        self.api_key = keys.get('rapidapi_key', '')
        self.base_url = "https://sky-scrapper.p.rapidapi.com/api/v1"
        self.headers = {
            'x-rapidapi-host': 'sky-scrapper.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Face request către API"""
        if not self.api_key:
            st.warning("⚠️ RapidAPI key nu este configurat")
            return {}
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            # Rate limiting
            if not cache_manager.can_call_api('rapidapi'):
                wait_time = cache_manager.get_rate_limiter('rapidapi').wait_time()
                time.sleep(wait_time)
            cache_manager.record_api_call('rapidapi')
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 429:
                st.error("❌ Rate limit depășit. Așteaptă câteva secunde.")
                return {}
            
            if response.status_code != 200:
                st.error(f"❌ Sky-Scrapper Error: {response.status_code}")
                return {}
            
            return response.json()
            
        except Exception as e:
            st.error(f"❌ Sky-Scrapper Error: {str(e)}")
            return {}
    
    def search_airport(self, query: str) -> List[dict]:
        """Caută aeroporturi după nume sau cod"""
        cache_key = ('sky_airport', query)
        cached = cache_manager.get('airports', *cache_key)
        if cached:
            return cached
        
        data = self._make_request('flights/searchAirport', {'query': query})
        
        airports = []
        if data.get('status') and data.get('data'):
            for item in data['data']:
                if item.get('navigation', {}).get('entityType') == 'AIRPORT':
                    airports.append({
                        'skyId': item.get('skyId'),
                        'entityId': item.get('entityId'),
                        'name': item.get('presentation', {}).get('title', ''),
                        'subtitle': item.get('presentation', {}).get('subtitle', ''),
                        'iata': item.get('skyId', '')
                    })
        
        cache_manager.set('airports', airports, *cache_key)
        return airports
    
    def search_flights(
        self,
        origin_sky_id: str,
        destination_sky_id: str,
        origin_entity_id: str,
        destination_entity_id: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = 'economy',
        currency: str = 'EUR'
    ) -> List[FlightOffer]:
        """Caută zboruri"""
        
        params = {
            'originSkyId': origin_sky_id,
            'destinationSkyId': destination_sky_id,
            'originEntityId': origin_entity_id,
            'destinationEntityId': destination_entity_id,
            'date': departure_date,
            'adults': adults,
            'currency': currency,
            'cabinClass': cabin_class
        }
        
        if return_date:
            params['returnDate'] = return_date
        if children > 0:
            params['childrens'] = children
        if infants > 0:
            params['infants'] = infants
        
        data = self._make_request('flights/searchFlights', params)
        
        return self._parse_flights(data, currency)
    
    def _parse_flights(self, data: dict, currency: str) -> List[FlightOffer]:
        """Parsează răspunsul API"""
        offers = []
        
        if not data.get('status') or not data.get('data'):
            return offers
        
        itineraries = data.get('data', {}).get('itineraries', [])
        
        for idx, itinerary in enumerate(itineraries[:50]):  # Limită 50
            try:
                legs = itinerary.get('legs', [])
                if not legs:
                    continue
                
                first_leg = legs[0]
                
                # Informații zbor
                origin = first_leg.get('origin', {}).get('displayCode', '')
                destination = first_leg.get('destination', {}).get('displayCode', '')
                
                # Timp
                departure_str = first_leg.get('departure', '')
                arrival_str = first_leg.get('arrival', '')
                
                try:
                    departure_time = datetime.fromisoformat(departure_str.replace('Z', ''))
                    arrival_time = datetime.fromisoformat(arrival_str.replace('Z', ''))
                except:
                    continue
                
                # Durată
                duration_minutes = first_leg.get('durationInMinutes', 0)
                hours = duration_minutes // 60
                minutes = duration_minutes % 60
                duration = f"{hours}h {minutes}m"
                
                # Companie
                carriers = first_leg.get('carriers', {}).get('marketing', [])
                airline = carriers[0].get('name', 'Unknown') if carriers else 'Unknown'
                airline_code = carriers[0].get('alternateId', '') if carriers else ''
                
                # Escale
                stops = first_leg.get('stopCount', 0)
                
                # Preț
                price_data = itinerary.get('price', {})
                price = price_data.get('raw', 0)
                
                # Link
                booking_link = itinerary.get('deepLink', '')
                
                offer = FlightOffer(
                    id=f"SKY-{idx}",
                    source='Skyscanner',
                    airline=airline,
                    airline_code=airline_code,
                    origin=origin,
                    destination=destination,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    duration=duration,
                    price=price,
                    currency=currency,
                    cabin_class='Economy',
                    stops=stops,
                    segments=[],
                    booking_link=booking_link
                )
                
                offers.append(offer)
                
            except Exception as e:
                continue
        
        return offers


# ============================================
# KIWI TEQUILA API
# ============================================

class TequilaAPI:
    """Client pentru Kiwi Tequila API"""
    
    def __init__(self):
        keys = Settings.get_api_keys()
        self.api_key = keys.get('tequila_key', '')
        self.base_url = "https://api.tequila.kiwi.com/v2"
        self.headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Face request către API"""
        if not self.api_key:
            return {}
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if not cache_manager.can_call_api('tequila'):
                wait_time = cache_manager.get_rate_limiter('tequila').wait_time()
                time.sleep(wait_time)
            cache_manager.record_api_call('tequila')
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return {}
            
            return response.json()
            
        except Exception as e:
            return {}
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = 'M',
        non_stop: bool = False,
        currency: str = 'EUR',
        max_results: int = 50
    ) -> List[FlightOffer]:
        """Caută zboruri cu Tequila"""
        
        params = {
            'fly_from': origin,
            'fly_to': destination,
            'date_from': departure_date,
            'date_to': departure_date,
            'adults': adults,
            'curr': currency,
            'limit': max_results,
            'selected_cabins': cabin_class
        }
        
        if return_date:
            params['return_from'] = return_date
            params['return_to'] = return_date
        if children > 0:
            params['children'] = children
        if infants > 0:
            params['infants'] = infants
        if non_stop:
            params['max_stopovers'] = 0
        
        data = self._make_request('search', params)
        
        return self._parse_flights(data, currency)
    
    def _parse_flights(self, data: dict, currency: str) -> List[FlightOffer]:
        """Parsează răspunsul Tequila"""
        offers = []
        
        if not data.get('data'):
            return offers
        
        for idx, flight in enumerate(data['data'][:50]):
            try:
                # Informații de bază
                route = flight.get('route', [])
                if not route:
                    continue
                
                first_segment = route[0]
                last_segment = route[-1]
                
                # Origine și destinație
                origin = first_segment.get('flyFrom', '')
                destination = last_segment.get('flyTo', '')
                
                # Timp
                departure_time = datetime.fromtimestamp(first_segment.get('dTime', 0))
                arrival_time = datetime.fromtimestamp(last_segment.get('aTime', 0))
                
                # Durată
                duration_seconds = flight.get('duration', {}).get('total', 0)
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                duration = f"{hours}h {minutes}m"
                
                # Companie
                airlines = flight.get('airlines', [])
                airline_code = airlines[0] if airlines else ''
                airline = airline_code  # Tequila nu dă numele complet
                
                # Escale
                stops = len(route) - 1
                
                # Preț
                price = flight.get('price', 0)
                
                # Link booking
                booking_link = flight.get('deep_link', '')
                
                offer = FlightOffer(
                    id=f"KIWI-{flight.get('id', idx)}",
                    source='Kiwi.com',
                    airline=airline,
                    airline_code=airline_code,
                    origin=origin,
                    destination=destination,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    duration=duration,
                    price=price,
                    currency=currency,
                    cabin_class='Economy',
                    stops=stops,
                    segments=[{
                        'from': seg.get('flyFrom'),
                        'to': seg.get('flyTo'),
                        'carrier': seg.get('airline'),
                        'flight_number': seg.get('flight_no'),
                    } for seg in route],
                    booking_link=booking_link,
                    seats_available=flight.get('availability', {}).get('seats')
                )
                
                offers.append(offer)
                
            except Exception:
                continue
        
        return offers


# ============================================
# AIRLABS API (pentru aeroporturi)
# ============================================

class AirLabsAPI:
    """Client pentru AirLabs API"""
    
    def __init__(self):
        self.config = Settings.get_airlabs_config()
        self.base_url = "https://airlabs.co/api/v9"
    
    def get_airports(self) -> List[dict]:
        """Obține lista de aeroporturi"""
        cached = cache_manager.get('airports', 'all_airports')
        if cached:
            return cached
        
        url = f"{self.base_url}/airports"
        params = {'api_key': self.config.key}
        
        try:
            if not cache_manager.can_call_api('airlabs'):
                time.sleep(cache_manager.get_rate_limiter('airlabs').wait_time())
            cache_manager.record_api_call('airlabs')
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                st.warning("⚠️ Nu s-au putut încărca aeroporturile de la AirLabs")
                return []
            
            data = response.json()
            airports = data.get('response', [])
            
            cache_manager.set('airports', airports, 'all_airports')
            return airports
            
        except Exception as e:
            st.error(f"❌ AirLabs Error: {str(e)}")
            return []


# ============================================
# SERVICIU PRINCIPAL
# ============================================

class FlightSearchService:
    """Serviciu principal pentru căutarea zborurilor"""
    
    def __init__(self):
        self.sky_scrapper = SkyScrapperAPI()
        self.tequila = TequilaAPI()
        self.airlabs = AirLabsAPI()
        self._airports_cache = {}
        self._sky_ids_cache = {}
    
    def _get_sky_ids(self, iata_code: str) -> tuple:
        """Obține Sky IDs pentru un aeroport"""
        if iata_code in self._sky_ids_cache:
            return self._sky_ids_cache[iata_code]
        
        results = self.sky_scrapper.search_airport(iata_code)
        
        if results:
            sky_id = results[0].get('skyId', iata_code)
            entity_id = results[0].get('entityId', '')
            self._sky_ids_cache[iata_code] = (sky_id, entity_id)
            return (sky_id, entity_id)
        
        return (iata_code, '')
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = 'M',
        non_stop: bool = False,
        currency: str = 'EUR',
        max_results: int = 50,
        sort_by: str = 'price'
    ) -> List[FlightOffer]:
        """Caută zboruri din toate sursele disponibile"""
        
        all_offers = []
        sources_tried = []
        sources_success = []
        
        # Mapare cabin class
        cabin_map_sky = {
            'M': 'economy',
            'W': 'premium_economy',
            'C': 'business',
            'F': 'first'
        }
        
        # 1. Încearcă Sky-Scrapper (Skyscanner)
        st.info("🔍 Se caută în Skyscanner...")
        sources_tried.append("Skyscanner")
        
        try:
            origin_sky, origin_entity = self._get_sky_ids(origin)
            dest_sky, dest_entity = self._get_sky_ids(destination)
            
            if origin_entity and dest_entity:
                sky_offers = self.sky_scrapper.search_flights(
                    origin_sky_id=origin_sky,
                    destination_sky_id=dest_sky,
                    origin_entity_id=origin_entity,
                    destination_entity_id=dest_entity,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=adults,
                    children=children,
                    infants=infants,
                    cabin_class=cabin_map_sky.get(cabin_class, 'economy'),
                    currency=currency
                )
                
                if sky_offers:
                    all_offers.extend(sky_offers)
                    sources_success.append(f"Skyscanner ({len(sky_offers)})")
                    st.success(f"✅ Skyscanner: {len(sky_offers)} zboruri")
        except Exception as e:
            st.warning(f"⚠️ Skyscanner: {str(e)}")
        
        # 2. Încearcă Kiwi Tequila
        keys = Settings.get_api_keys()
        if keys.get('tequila_key'):
            st.info("🔍 Se caută în Kiwi.com...")
            sources_tried.append("Kiwi.com")
            
            try:
                tequila_offers = self.tequila.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=adults,
                    children=children,
                    infants=infants,
                    cabin_class=cabin_class,
                    non_stop=non_stop,
                    currency=currency,
                    max_results=max_results
                )
                
                if tequila_offers:
                    all_offers.extend(tequila_offers)
                    sources_success.append(f"Kiwi.com ({len(tequila_offers)})")
                    st.success(f"✅ Kiwi.com: {len(tequila_offers)} zboruri")
            except Exception as e:
                st.warning(f"⚠️ Kiwi.com: {str(e)}")
        
        # Filtrare zboruri directe
        if non_stop:
            all_offers = [o for o in all_offers if o.stops == 0]
        
        # Sortare
        if sort_by == 'price':
            all_offers.sort(key=lambda x: x.price)
        elif sort_by == 'duration':
            all_offers.sort(key=lambda x: x.departure_time)
        elif sort_by == 'stops':
            all_offers.sort(key=lambda x: (x.stops, x.price))
        
        # Elimină duplicatele (aproximativ - după preț și oră)
        seen = set()
        unique_offers = []
        for offer in all_offers:
            key = (offer.price, offer.departure_time.strftime('%H:%M'), offer.stops)
            if key not in seen:
                seen.add(key)
                unique_offers.append(offer)
        
        # Rezumat
        if sources_success:
            st.success(f"📊 Total: {len(unique_offers)} zboruri din {', '.join(sources_success)}")
        else:
            st.warning(f"⚠️ Nu s-au găsit zboruri. Surse încercate: {', '.join(sources_tried)}")
        
        # Actualizează monitorul de prețuri
        if unique_offers:
            route_key = f"{origin}-{destination}-{departure_date}"
            min_price = min(o.price for o in unique_offers)
            cache_manager.update_price_history(route_key, min_price)
        
        return unique_offers[:max_results]
    
    def get_all_airports(self) -> Dict[str, Dict[str, List[dict]]]:
        """Obține toate aeroporturile organizate pe continente și țări"""
        if self._airports_cache:
            return self._airports_cache
        
        organized = {
            "Europa": {},
            "Asia": {},
            "Africa": {},
            "America de Nord": {},
            "America de Sud": {},
            "Oceania": {},
            "Altele": {}
        }
        
        try:
            airports = self.airlabs.get_airports()
            
            if not airports:
                st.warning("⚠️ Nu s-au putut încărca aeroporturile")
                return organized
            
            for airport in airports:
                if not airport.get('iata_code'):
                    continue
                
                country_code = airport.get('country_code', 'XX')
                country_name = get_country_name(country_code)
                continent_code = get_continent_code(country_code)
                continent_name = get_continent_name(continent_code)
                
                if continent_name not in organized:
                    continent_name = "Altele"
                
                if country_name not in organized[continent_name]:
                    organized[continent_name][country_name] = []
                
                organized[continent_name][country_name].append({
                    'iata': airport.get('iata_code'),
                    'name': airport.get('name', 'N/A'),
                    'city': airport.get('city', 'N/A'),
                    'lat': airport.get('lat'),
                    'lng': airport.get('lng')
                })
            
            # Sortare
            for continent in organized:
                organized[continent] = dict(sorted(organized[continent].items()))
                for country in organized[continent]:
                    organized[continent][country].sort(key=lambda x: x['name'])
            
            organized = {k: v for k, v in organized.items() if v}
            
            self._airports_cache = organized
            return organized
            
        except Exception as e:
            st.error(f"❌ Error loading airports: {e}")
            return {}
    
    def add_price_monitor(self, origin: str, destination: str, 
                          departure_date: str, target_price: Optional[float] = None):
        route_key = f"{origin}-{destination}-{departure_date}"
        search_params = {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date
        }
        cache_manager.add_price_monitor(route_key, search_params, target_price)
    
    def get_monitored_routes(self) -> Dict[str, dict]:
        return cache_manager.get_price_monitors()
    
    def get_price_history(self, route_key: str) -> List[dict]:
        return cache_manager.get_price_history(route_key)
