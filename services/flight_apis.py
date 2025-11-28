"""
Servicii pentru căutarea zborurilor - Sky-Scrapper (Skyscanner via RapidAPI)
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import streamlit as st

from config.settings import Settings
from .cache_manager import cache_manager


# ============================================
# DICȚIONARE ȚĂRI ȘI CONTINENTE  
# ============================================

COUNTRY_NAMES = {
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
    "AR": "Argentina", "BO": "Bolivia", "BR": "Brazilia", "CL": "Chile",
    "CO": "Columbia", "EC": "Ecuador", "FK": "Insulele Falkland",
    "GF": "Guyana Franceză", "GY": "Guyana", "PE": "Peru", "PY": "Paraguay",
    "SR": "Surinam", "UY": "Uruguay", "VE": "Venezuela",
    "AS": "Samoa Americană", "AU": "Australia", "CK": "Insulele Cook",
    "FJ": "Fiji", "FM": "Micronezia", "GU": "Guam", "KI": "Kiribati",
    "MH": "Insulele Marshall", "NC": "Noua Caledonie", "NF": "Insula Norfolk",
    "NR": "Nauru", "NU": "Niue", "NZ": "Noua Zeelandă", "PF": "Polinezia Franceză",
    "PG": "Papua Noua Guinee", "PN": "Insulele Pitcairn", "PW": "Palau",
    "SB": "Insulele Solomon", "TO": "Tonga", "TV": "Tuvalu", "VU": "Vanuatu",
    "WF": "Wallis și Futuna", "WS": "Samoa",
}

CONTINENT_MAPPING = {
    "AD": "EU", "AL": "EU", "AT": "EU", "BA": "EU", "BE": "EU", "BG": "EU",
    "BY": "EU", "CH": "EU", "CY": "EU", "CZ": "EU", "DE": "EU", "DK": "EU",
    "EE": "EU", "ES": "EU", "FI": "EU", "FO": "EU", "FR": "EU", "GB": "EU",
    "GI": "EU", "GR": "EU", "HR": "EU", "HU": "EU", "IE": "EU", "IS": "EU",
    "IT": "EU", "LI": "EU", "LT": "EU", "LU": "EU", "LV": "EU", "MC": "EU",
    "MD": "EU", "ME": "EU", "MK": "EU", "MT": "EU", "NL": "EU", "NO": "EU",
    "PL": "EU", "PT": "EU", "RO": "EU", "RS": "EU", "RU": "EU", "SE": "EU",
    "SI": "EU", "SK": "EU", "SM": "EU", "UA": "EU", "VA": "EU", "XK": "EU",
    "AE": "AS", "AF": "AS", "AM": "AS", "AZ": "AS", "BD": "AS", "BH": "AS",
    "BN": "AS", "BT": "AS", "CN": "AS", "GE": "AS", "HK": "AS", "ID": "AS",
    "IL": "AS", "IN": "AS", "IQ": "AS", "IR": "AS", "JO": "AS", "JP": "AS",
    "KG": "AS", "KH": "AS", "KP": "AS", "KR": "AS", "KW": "AS", "KZ": "AS",
    "LA": "AS", "LB": "AS", "LK": "AS", "MM": "AS", "MN": "AS", "MO": "AS",
    "MV": "AS", "MY": "AS", "NP": "AS", "OM": "AS", "PH": "AS", "PK": "AS",
    "PS": "AS", "QA": "AS", "SA": "AS", "SG": "AS", "SY": "AS", "TH": "AS",
    "TJ": "AS", "TL": "AS", "TM": "AS", "TR": "AS", "TW": "AS", "UZ": "AS",
    "VN": "AS", "YE": "AS",
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
    "AG": "NA", "AI": "NA", "AW": "NA", "BB": "NA", "BM": "NA", "BS": "NA",
    "BZ": "NA", "CA": "NA", "CR": "NA", "CU": "NA", "CW": "NA", "DM": "NA",
    "DO": "NA", "GD": "NA", "GL": "NA", "GP": "NA", "GT": "NA", "HN": "NA",
    "HT": "NA", "JM": "NA", "KN": "NA", "KY": "NA", "LC": "NA", "MQ": "NA",
    "MS": "NA", "MX": "NA", "NI": "NA", "PA": "NA", "PM": "NA", "PR": "NA",
    "SV": "NA", "SX": "NA", "TC": "NA", "TT": "NA", "US": "NA", "VC": "NA",
    "VG": "NA", "VI": "NA",
    "AR": "SA", "BO": "SA", "BR": "SA", "CL": "SA", "CO": "SA", "EC": "SA",
    "FK": "SA", "GF": "SA", "GY": "SA", "PE": "SA", "PY": "SA", "SR": "SA",
    "UY": "SA", "VE": "SA",
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
# MODEL FLIGHT OFFER
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
            'Plecare': self.departure_time.strftime('%d/%m/%Y %H:%M'),
            'Sosire': self.arrival_time.strftime('%d/%m/%Y %H:%M'),
            'Durată': self.duration,
            'Preț': self.price,
            'Monedă': self.currency,
            'Clasă': self.cabin_class,
            'Escale': self.stops,
            'Locuri': self.seats_available or 'N/A',
        }


# ============================================
# SKY-SCRAPPER API (Skyscanner via RapidAPI)
# ============================================

class SkyScrapperAPI:
    """Client pentru Sky-Scrapper API (Skyscanner via RapidAPI)"""
    
    def __init__(self):
        keys = Settings.get_api_keys()
        self.api_key = keys.get('rapidapi_key', '')
        self.base_url = "https://sky-scrapper.p.rapidapi.com/api/v1"
        self.headers = {
            'x-rapidapi-host': 'sky-scrapper.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
        self._entity_cache = {}
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Face request către API"""
        if not self.api_key:
            st.error("❌ RapidAPI key nu este configurat!")
            return {}
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=30
            )
            
            # Debug info
            with st.expander("🔧 Debug API Request", expanded=False):
                st.write(f"**URL:** {response.url}")
                st.write(f"**Status:** {response.status_code}")
            
            if response.status_code == 429:
                st.error("❌ Rate limit depășit. Așteaptă 1 minut și încearcă din nou.")
                return {}
            
            if response.status_code != 200:
                st.error(f"❌ API Error: {response.status_code} - {response.text[:200]}")
                return {}
            
            data = response.json()
            return data
            
        except requests.exceptions.Timeout:
            st.error("❌ Timeout - Serverul nu a răspuns în timp util")
            return {}
        except Exception as e:
            st.error(f"❌ Eroare conexiune: {str(e)}")
            return {}
    
    def search_airport(self, query: str) -> Optional[dict]:
        """Caută un aeroport după cod IATA și returnează entityId"""
        
        # Verifică cache
        if query.upper() in self._entity_cache:
            return self._entity_cache[query.upper()]
        
        params = {'query': query, 'locale': 'en-US'}
        data = self._make_request('flights/searchAirport', params)
        
        if not data.get('status') or not data.get('data'):
            return None
        
        # Caută aeroportul exact
        for item in data['data']:
            nav = item.get('navigation', {})
            if nav.get('entityType') == 'AIRPORT':
                result = {
                    'skyId': item.get('skyId'),
                    'entityId': item.get('entityId'),
                    'name': item.get('presentation', {}).get('title', ''),
                }
                self._entity_cache[query.upper()] = result
                return result
        
        return None
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = 'economy',
        currency: str = 'EUR'
    ) -> List[FlightOffer]:
        """Caută zboruri"""
        
        # Obține entity IDs
        st.info(f"🔍 Se caută aeroportul {origin}...")
        origin_data = self.search_airport(origin)
        
        st.info(f"🔍 Se caută aeroportul {destination}...")
        dest_data = self.search_airport(destination)
        
        if not origin_data:
            st.error(f"❌ Nu s-a găsit aeroportul: {origin}")
            return []
        
        if not dest_data:
            st.error(f"❌ Nu s-a găsit aeroportul: {destination}")
            return []
        
        st.success(f"✅ Aeroporturi găsite: {origin_data['name']} → {dest_data['name']}")
        
        # Parametri căutare
        params = {
            'originSkyId': origin_data['skyId'],
            'destinationSkyId': dest_data['skyId'],
            'originEntityId': origin_data['entityId'],
            'destinationEntityId': dest_data['entityId'],
            'date': departure_date,
            'adults': str(adults),
            'currency': currency,
            'cabinClass': cabin_class,
            'countryCode': 'RO',
            'market': 'ro-RO'
        }
        
        if return_date:
            params['returnDate'] = return_date
        if children > 0:
            params['childrens'] = str(children)
        if infants > 0:
            params['infants'] = str(infants)
        
        st.info("🔍 Se caută zboruri...")
        data = self._make_request('flights/searchFlights', params)
        
        if not data:
            return []
        
        return self._parse_flights(data, currency)
    
    def _parse_flights(self, data: dict, currency: str) -> List[FlightOffer]:
        """Parsează răspunsul API"""
        offers = []
        
        if not data.get('status'):
            st.warning("⚠️ API nu a returnat date valide")
            return offers
        
        itineraries = data.get('data', {}).get('itineraries', [])
        
        if not itineraries:
            st.warning("⚠️ Nu s-au găsit zboruri pentru această rută")
            return offers
        
        st.info(f"📊 Se procesează {len(itineraries)} rezultate...")
        
        for idx, itinerary in enumerate(itineraries[:100]):
            try:
                legs = itinerary.get('legs', [])
                if not legs:
                    continue
                
                first_leg = legs[0]
                
                # Origine și destinație
                origin = first_leg.get('origin', {}).get('displayCode', '')
                destination = first_leg.get('destination', {}).get('displayCode', '')
                
                # Timp plecare/sosire
                departure_str = first_leg.get('departure', '')
                arrival_str = first_leg.get('arrival', '')
                
                if not departure_str or not arrival_str:
                    continue
                
                # Parse datetime
                try:
                    # Format: 2024-12-25T10:30:00
                    departure_time = datetime.fromisoformat(departure_str.replace('Z', ''))
                    arrival_time = datetime.fromisoformat(arrival_str.replace('Z', ''))
                except:
                    continue
                
                # Durată
                duration_minutes = first_leg.get('durationInMinutes', 0)
                hours = duration_minutes // 60
                minutes = duration_minutes % 60
                duration = f"{hours}h {minutes}m"
                
                # Companie aeriană
                carriers = first_leg.get('carriers', {}).get('marketing', [])
                if carriers:
                    airline = carriers[0].get('name', 'Unknown')
                    airline_code = carriers[0].get('alternateId', '')
                    # Logo URL: carriers[0].get('logoUrl', '')
                else:
                    airline = 'Unknown'
                    airline_code = ''
                
                # Număr escale
                stops = first_leg.get('stopCount', 0)
                
                # Preț
                price_data = itinerary.get('price', {})
                price = price_data.get('raw', 0)
                price_formatted = price_data.get('formatted', '')
                
                if price == 0:
                    continue
                
                # Segmente zbor
                segments_data = first_leg.get('segments', [])
                segments = []
                for seg in segments_data:
                    segments.append({
                        'from': seg.get('origin', {}).get('displayCode', ''),
                        'to': seg.get('destination', {}).get('displayCode', ''),
                        'carrier': seg.get('operatingCarrier', {}).get('name', ''),
                        'flight_number': seg.get('flightNumber', ''),
                        'departure': seg.get('departure', ''),
                        'arrival': seg.get('arrival', ''),
                    })
                
                offer = FlightOffer(
                    id=f"SKY-{idx+1}",
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
                    cabin_class=cabin_class if 'cabin_class' in dir() else 'Economy',
                    stops=stops,
                    segments=segments,
                    booking_link=None
                )
                
                offers.append(offer)
                
            except Exception as e:
                # Skip invalid entries silently
                continue
        
        return offers


# ============================================
# AIRLABS API (pentru aeroporturi)
# ============================================

class AirLabsAPI:
    """Client pentru AirLabs API - lista aeroporturi"""
    
    def __init__(self):
        self.config = Settings.get_airlabs_config()
        self.base_url = "https://airlabs.co/api/v9"
    
    def get_airports(self) -> List[dict]:
        """Obține lista de aeroporturi"""
        cached = cache_manager.get('airports', 'all_airports_v2')
        if cached:
            return cached
        
        url = f"{self.base_url}/airports"
        params = {'api_key': self.config.key}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                st.warning(f"⚠️ AirLabs Error: {response.status_code}")
                return []
            
            data = response.json()
            airports = data.get('response', [])
            
            if airports:
                cache_manager.set('airports', airports, 'all_airports_v2')
            
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
        cabin_class: str = 'economy',
        non_stop: bool = False,
        currency: str = 'EUR',
        max_results: int = 50,
        sort_by: str = 'price'
    ) -> List[FlightOffer]:
        """Caută zboruri"""
        
        # Căutare Sky-Scrapper
        offers = self.sky_scrapper.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            currency=currency
        )
        
        # Filtrare zboruri directe
        if non_stop:
            offers = [o for o in offers if o.stops == 0]
            st.info(f"✈️ Filtrat: {len(offers)} zboruri directe")
        
        # Sortare
        if sort_by == 'price':
            offers.sort(key=lambda x: x.price)
        elif sort_by == 'duration':
            # Sortare după durată
            offers.sort(key=lambda x: x.departure_time)
        elif sort_by == 'stops':
            offers.sort(key=lambda x: (x.stops, x.price))
        
        # Actualizează monitorul de prețuri
        if offers:
            route_key = f"{origin}-{destination}-{departure_date}"
            min_price = min(o.price for o in offers)
            cache_manager.update_price_history(route_key, min_price)
            st.success(f"✅ Găsite {len(offers)} zboruri! Cel mai ieftin: {min_price:.2f} {currency}")
        
        return offers[:max_results]
    
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
                return organized
            
            for airport in airports:
                iata = airport.get('iata_code')
                if not iata:
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
                    'iata': iata,
                    'name': airport.get('name', 'N/A'),
                    'city': airport.get('city', 'N/A'),
                    'lat': airport.get('lat'),
                    'lng': airport.get('lng')
                })
            
            # Sortare
            for continent in list(organized.keys()):
                if not organized[continent]:
                    del organized[continent]
                    continue
                organized[continent] = dict(sorted(organized[continent].items()))
                for country in organized[continent]:
                    organized[continent][country].sort(key=lambda x: x.get('name', ''))
            
            self._airports_cache = organized
            return organized
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
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
