"""
Servicii pentru căutarea zborurilor folosind API-uri oficiale
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import streamlit as st

from config.settings import Settings
from .cache_manager import cache_manager


# Dicționar complet cu toate țările din lume
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

# Mapping continente
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
    "AN": "Antarctica",
    "AS": "Asia",
    "EU": "Europa",
    "NA": "America de Nord",
    "OC": "Oceania",
    "SA": "America de Sud"
}


def get_country_name(country_code: str) -> str:
    """Convertește codul țării în nume complet"""
    return COUNTRY_NAMES.get(country_code.upper(), country_code)


def get_continent_code(country_code: str) -> str:
    """Obține codul continentului pentru o țară"""
    return CONTINENT_MAPPING.get(country_code.upper(), "EU")


def get_continent_name(continent_code: str) -> str:
    """Convertește codul continentului în nume"""
    return CONTINENT_NAMES.get(continent_code.upper(), continent_code)


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
        """Convertește în dicționar pentru DataFrame"""
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
            'Locuri': self.seats_available or 'N/A'
        }


class APIError(Exception):
    """Excepție pentru erori API"""
    def __init__(self, message: str, status_code: int = None, api_name: str = None):
        self.message = message
        self.status_code = status_code
        self.api_name = api_name
        super().__init__(self.message)


class BaseAPI:
    """Clasă de bază pentru API-uri"""
    
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _check_rate_limit(self):
        """Verifică și aplică rate limiting"""
        if not cache_manager.can_call_api(self.name):
            wait_time = cache_manager.get_rate_limiter(self.name).wait_time()
            if wait_time > 0:
                time.sleep(wait_time)
        cache_manager.record_api_call(self.name)


class AmadeusAPI(BaseAPI):
    """Client pentru Amadeus Flight Offers Search API"""
    
    def __init__(self):
        super().__init__('amadeus')
        self.config = Settings.get_amadeus_config()
        self.base_url = "https://api.amadeus.com"
        self._token = None
        self._token_expires = None
    
    def _get_access_token(self) -> str:
        """Obține token de acces OAuth2"""
        # Verifică cache
        cached_token = cache_manager.get('token', 'amadeus')
        if cached_token:
            return cached_token
        
        url = f"{self.base_url}/v1/security/oauth2/token"
        
        try:
            response = requests.post(
                url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.config.key,
                    'client_secret': self.config.secret
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code != 200:
                st.error(f"❌ Amadeus Auth Error: {response.status_code} - {response.text}")
                raise APIError(f"Failed to get Amadeus token: {response.text}", 
                              response.status_code, self.name)
            
            data = response.json()
            token = data['access_token']
            
            # Salvează în cache
            cache_manager.set('token', token, 'amadeus')
            
            return token
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Amadeus Connection Error: {str(e)}")
            raise APIError(f"Connection error: {str(e)}", api_name=self.name)
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = 'ECONOMY',
        non_stop: bool = False,
        currency: str = 'EUR',
        max_results: int = 50
    ) -> List[FlightOffer]:
        """Caută zboruri folosind Amadeus API"""
        
        # Verifică cache
        cache_key = (origin, destination, departure_date, return_date, 
                    adults, cabin_class, non_stop)
        cached = cache_manager.get('flights', *cache_key, 'amadeus')
        if cached:
            st.info("📦 Rezultate din cache")
            return cached
        
        # Debug info
        with st.expander("🔧 Debug Info", expanded=False):
            st.write(f"**Origin:** {origin}")
            st.write(f"**Destination:** {destination}")
            st.write(f"**Date:** {departure_date}")
            st.write(f"**API Key:** {self.config.key[:10]}..." if self.config.key else "❌ No API Key")
            st.write(f"**API Secret:** {self.config.secret[:5]}..." if self.config.secret else "❌ No API Secret")
        
        try:
            # Obține token
            st.info("🔑 Se obține token-ul Amadeus...")
            token = self._get_access_token()
            st.success("✅ Token obținut!")
            
            self.session.headers.update({'Authorization': f'Bearer {token}'})
            
            url = f"{self.base_url}/v2/shopping/flight-offers"
            
            params = {
                'originLocationCode': origin.upper(),
                'destinationLocationCode': destination.upper(),
                'departureDate': departure_date,
                'adults': adults,
                'travelClass': cabin_class,
                'currencyCode': currency,
                'max': min(max_results, 250)  # Amadeus max is 250
            }
            
            if return_date:
                params['returnDate'] = return_date
            if children > 0:
                params['children'] = children
            if infants > 0:
                params['infants'] = infants
            if non_stop:
                params['nonStop'] = 'true'
            
            st.info(f"🔍 Se caută zboruri {origin} → {destination}...")
            
            # Rate limiting
            self._check_rate_limit()
            
            response = self.session.get(url, params=params, timeout=60)
            
            # Debug response
            with st.expander("📡 API Response", expanded=False):
                st.write(f"**Status Code:** {response.status_code}")
                st.write(f"**URL:** {response.url}")
            
            if response.status_code == 401:
                st.error("❌ Token invalid sau expirat. Se reîncearcă...")
                cache_manager.set('token', None, 'amadeus')  # Clear cached token
                token = self._get_access_token()
                self.session.headers.update({'Authorization': f'Bearer {token}'})
                response = self.session.get(url, params=params, timeout=60)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        error_msg = error_data['errors'][0].get('detail', error_msg)
                except:
                    pass
                st.error(f"❌ Amadeus API Error ({response.status_code}): {error_msg}")
                return []
            
            data = response.json()
            
            # Debug data
            with st.expander("📊 Raw Data", expanded=False):
                st.write(f"**Total offers:** {len(data.get('data', []))}")
                if data.get('data'):
                    st.json(data['data'][0])  # Show first offer
            
            offers = self._parse_flight_offers(data)
            
            if offers:
                st.success(f"✅ Găsite {len(offers)} zboruri!")
                # Salvează în cache
                cache_manager.set('flights', offers, *cache_key, 'amadeus')
            else:
                st.warning("⚠️ Nu s-au găsit zboruri pentru această rută.")
            
            return offers
            
        except APIError as e:
            st.error(f"❌ API Error: {e.message}")
            return []
        except Exception as e:
            st.error(f"❌ Unexpected Error: {str(e)}")
            import traceback
            with st.expander("🐛 Error Details"):
                st.code(traceback.format_exc())
            return []
    
    def _parse_flight_offers(self, data: dict) -> List[FlightOffer]:
        """Parsează răspunsul Amadeus"""
        offers = []
        
        carriers = data.get('dictionaries', {}).get('carriers', {})
        
        for offer in data.get('data', []):
            try:
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                first_segment = segments[0]
                last_segment = segments[-1]
                
                stops = len(segments) - 1
                
                airline_code = first_segment['carrierCode']
                airline_name = carriers.get(airline_code, airline_code)
                
                # Parse times - handle different formats
                dep_str = first_segment['departure']['at']
                arr_str = last_segment['arrival']['at']
                
                # Remove timezone info if present
                if '+' in dep_str:
                    dep_str = dep_str.split('+')[0]
                if '+' in arr_str:
                    arr_str = arr_str.split('+')[0]
                if 'Z' in dep_str:
                    dep_str = dep_str.replace('Z', '')
                if 'Z' in arr_str:
                    arr_str = arr_str.replace('Z', '')
                
                departure = datetime.fromisoformat(dep_str)
                arrival = datetime.fromisoformat(arr_str)
                
                # Duration
                duration = itinerary.get('duration', '')
                if duration.startswith('PT'):
                    # Parse PT2H30M format
                    duration = duration[2:]  # Remove PT
                    hours = 0
                    minutes = 0
                    if 'H' in duration:
                        h_part = duration.split('H')[0]
                        hours = int(h_part)
                        duration = duration.split('H')[1]
                    if 'M' in duration:
                        m_part = duration.replace('M', '')
                        if m_part:
                            minutes = int(m_part)
                    duration = f"{hours}h {minutes}m"
                
                # Price
                price_info = offer['price']
                price = float(price_info['total'])
                currency = price_info['currency']
                
                # Cabin class
                cabin = 'ECONOMY'
                if segments[0].get('travelerPricings'):
                    cabin = segments[0]['travelerPricings'][0].get('fareDetailsBySegment', [{}])[0].get('cabin', 'ECONOMY')
                
                # Seats
                seats = offer.get('numberOfBookableSeats')
                
                flight_offer = FlightOffer(
                    id=offer['id'],
                    source='Amadeus',
                    airline=airline_name,
                    airline_code=airline_code,
                    origin=first_segment['departure']['iataCode'],
                    destination=last_segment['arrival']['iataCode'],
                    departure_time=departure,
                    arrival_time=arrival,
                    duration=duration,
                    price=price,
                    currency=currency,
                    cabin_class=cabin,
                    stops=stops,
                    segments=[{
                        'from': seg['departure']['iataCode'],
                        'to': seg['arrival']['iataCode'],
                        'carrier': seg['carrierCode'],
                        'flight_number': seg.get('number', ''),
                        'departure': seg['departure']['at'],
                        'arrival': seg['arrival']['at']
                    } for seg in segments],
                    seats_available=seats
                )
                
                offers.append(flight_offer)
                
            except (KeyError, ValueError, TypeError) as e:
                st.warning(f"⚠️ Eroare la parsarea ofertei: {str(e)}")
                continue
        
        return offers


class AirLabsAPI(BaseAPI):
    """Client pentru AirLabs API"""
    
    def __init__(self):
        super().__init__('airlabs')
        self.config = Settings.get_airlabs_config()
        self.base_url = "https://airlabs.co/api/v9"
    
    def get_airports(self, country_code: Optional[str] = None) -> List[dict]:
        """Obține lista de aeroporturi"""
        cache_key = ('airports', country_code or 'all')
        cached = cache_manager.get('airports', *cache_key)
        if cached:
            return cached
        
        url = f"{self.base_url}/airports"
        params = {'api_key': self.config.key}
        
        if country_code:
            params['country_code'] = country_code.upper()
        
        try:
            self._check_rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                st.error(f"❌ AirLabs Error: {response.status_code}")
                return []
            
            data = response.json()
            airports = data.get('response', [])
            
            cache_manager.set('airports', airports, *cache_key)
            return airports
            
        except Exception as e:
            st.error(f"❌ AirLabs Error: {str(e)}")
            return []
    
    def get_airlines(self) -> List[dict]:
        """Obține lista de companii aeriene"""
        cached = cache_manager.get('airports', 'airlines')
        if cached:
            return cached
        
        url = f"{self.base_url}/airlines"
        params = {'api_key': self.config.key}
        
        try:
            self._check_rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            airlines = data.get('response', [])
            
            cache_manager.set('airports', airlines, 'airlines')
            return airlines
            
        except Exception:
            return []


class FlightSearchService:
    """Serviciu principal pentru căutarea zborurilor"""
    
    def __init__(self):
        self.amadeus = AmadeusAPI()
        self.airlabs = AirLabsAPI()
        self._airports_cache = {}
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = 'ECONOMY',
        non_stop: bool = False,
        currency: str = 'EUR',
        max_results: int = 50,
        sort_by: str = 'price'
    ) -> List[FlightOffer]:
        """Caută zboruri din toate sursele disponibile"""
        
        all_offers = []
        
        # Căutare Amadeus
        amadeus_offers = self.amadeus.search_flights(
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
        all_offers.extend(amadeus_offers)
        
        # Sortare
        if sort_by == 'price':
            all_offers.sort(key=lambda x: x.price)
        elif sort_by == 'duration':
            all_offers.sort(key=lambda x: x.departure_time)
        elif sort_by == 'stops':
            all_offers.sort(key=lambda x: (x.stops, x.price))
        
        # Actualizează monitorul de prețuri
        if all_offers:
            route_key = f"{origin}-{destination}-{departure_date}"
            min_price = min(o.price for o in all_offers)
            cache_manager.update_price_history(route_key, min_price)
        
        return all_offers[:max_results]
    
    def get_all_airports(self) -> Dict[str, Dict[str, List[dict]]]:
        """Obține toate aeroporturile organizate pe continente și țări"""
        if self._airports_cache:
            return self._airports_cache
        
        # Inițializare structură
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
                st.warning("⚠️ Nu s-au putut încărca aeroporturile de la AirLabs")
                return organized
            
            for airport in airports:
                if not airport.get('iata_code'):
                    continue
                
                country_code = airport.get('country_code', 'XX')
                
                # Obține numele țării
                country_name = get_country_name(country_code)
                
                # Obține continentul
                continent_code = get_continent_code(country_code)
                continent_name = get_continent_name(continent_code)
                
                # Mapare nume continent
                continent_map = {
                    "Europa": "Europa",
                    "Asia": "Asia", 
                    "Africa": "Africa",
                    "America de Nord": "America de Nord",
                    "America de Sud": "America de Sud",
                    "Oceania": "Oceania"
                }
                
                final_continent = continent_map.get(continent_name, "Altele")
                
                if final_continent not in organized:
                    final_continent = "Altele"
                
                if country_name not in organized[final_continent]:
                    organized[final_continent][country_name] = []
                
                organized[final_continent][country_name].append({
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
            
            # Elimină continentele goale
            organized = {k: v for k, v in organized.items() if v}
            
            self._airports_cache = organized
            return organized
            
        except Exception as e:
            st.error(f"❌ Error loading airports: {e}")
            return {}
    
    def add_price_monitor(self, origin: str, destination: str, 
                          departure_date: str, target_price: Optional[float] = None):
        """Adaugă un monitor de prețuri"""
        route_key = f"{origin}-{destination}-{departure_date}"
        search_params = {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date
        }
        cache_manager.add_price_monitor(route_key, search_params, target_price)
    
    def get_monitored_routes(self) -> Dict[str, dict]:
        """Returnează rutele monitorizate"""
        return cache_manager.get_price_monitors()
    
    def get_price_history(self, route_key: str) -> List[dict]:
        """Returnează istoricul prețurilor"""
        return cache_manager.get_price_history(route_key)
