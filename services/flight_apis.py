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


@dataclass
class FlightOffer:
    """Reprezintă o ofertă de zbor"""
    id: str
    source: str  # API source
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.Timeout, 
                                        requests.exceptions.ConnectionError))
    )
    def _make_request(self, method: str, url: str, **kwargs) -> dict:
        """Face un request cu retry și error handling"""
        self._check_rate_limit()
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                raise APIError("Rate limit exceeded", 429, self.name)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            raise APIError(f"HTTP Error: {str(e)}", response.status_code, self.name)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request Error: {str(e)}", api_name=self.name)


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
        
        response = requests.post(
            url,
            data={
                'grant_type': 'client_credentials',
                'client_id': self.config.key,
                'client_secret': self.config.secret
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code != 200:
            raise APIError(f"Failed to get Amadeus token: {response.text}", 
                          response.status_code, self.name)
        
        data = response.json()
        token = data['access_token']
        
        # Salvează în cache
        cache_manager.set('token', token, 'amadeus')
        
        return token
    
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
        """
        Caută zboruri folosind Amadeus API
        
        Args:
            origin: Codul IATA al aeroportului de plecare
            destination: Codul IATA al aeroportului de sosire
            departure_date: Data plecării (YYYY-MM-DD)
            return_date: Data întoarcerii (opțional)
            adults: Număr adulți
            children: Număr copii
            infants: Număr bebeluși
            cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            non_stop: Doar zboruri directe
            currency: Moneda pentru prețuri
            max_results: Număr maxim de rezultate
        """
        # Verifică cache
        cache_key = (origin, destination, departure_date, return_date, 
                    adults, cabin_class, non_stop)
        cached = cache_manager.get('flights', *cache_key, 'amadeus')
        if cached:
            return cached
        
        token = self._get_access_token()
        self.session.headers.update({'Authorization': f'Bearer {token}'})
        
        url = f"{self.base_url}/v2/shopping/flight-offers"
        
        params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': adults,
            'travelClass': cabin_class,
            'currencyCode': currency,
            'max': max_results
        }
        
        if return_date:
            params['returnDate'] = return_date
        if children > 0:
            params['children'] = children
        if infants > 0:
            params['infants'] = infants
        if non_stop:
            params['nonStop'] = 'true'
        
        try:
            data = self._make_request('GET', url, params=params)
            offers = self._parse_flight_offers(data)
            
            # Salvează în cache
            cache_manager.set('flights', offers, *cache_key, 'amadeus')
            
            return offers
            
        except APIError as e:
            st.error(f"Amadeus API Error: {e.message}")
            return []
    
    def _parse_flight_offers(self, data: dict) -> List[FlightOffer]:
        """Parsează răspunsul Amadeus"""
        offers = []
        
        # Dicționar pentru carriers
        carriers = data.get('dictionaries', {}).get('carriers', {})
        
        for offer in data.get('data', []):
            try:
                # Prima iterare (outbound)
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                first_segment = segments[0]
                last_segment = segments[-1]
                
                # Calculează numărul de escale
                stops = len(segments) - 1
                
                # Airline info
                airline_code = first_segment['carrierCode']
                airline_name = carriers.get(airline_code, airline_code)
                
                # Parse times
                departure = datetime.fromisoformat(
                    first_segment['departure']['at'].replace('Z', '+00:00')
                )
                arrival = datetime.fromisoformat(
                    last_segment['arrival']['at'].replace('Z', '+00:00')
                )
                
                # Duration
                duration = itinerary.get('duration', '')
                if duration.startswith('PT'):
                    duration = duration[2:].lower().replace('h', 'h ').replace('m', 'm')
                
                # Price
                price_info = offer['price']
                price = float(price_info['total'])
                currency = price_info['currency']
                
                # Cabin class
                cabin = segments[0].get('cabin', 'ECONOMY')
                
                # Seats
                seats = None
                if 'numberOfBookableSeats' in offer:
                    seats = offer['numberOfBookableSeats']
                
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
                
            except (KeyError, ValueError) as e:
                continue  # Skip malformed offers
        
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
            data = self._make_request('GET', url, params=params)
            airports = data.get('response', [])
            
            cache_manager.set('airports', airports, *cache_key)
            return airports
            
        except APIError as e:
            st.error(f"AirLabs API Error: {e.message}")
            return []
    
    def get_airlines(self) -> List[dict]:
        """Obține lista de companii aeriene"""
        cached = cache_manager.get('airports', 'airlines')
        if cached:
            return cached
        
        url = f"{self.base_url}/airlines"
        params = {'api_key': self.config.key}
        
        try:
            data = self._make_request('GET', url, params=params)
            airlines = data.get('response', [])
            
            cache_manager.set('airports', airlines, 'airlines')
            return airlines
            
        except APIError as e:
            st.error(f"AirLabs API Error: {e.message}")
            return []
    
    def get_routes(self, dep_iata: str) -> List[dict]:
        """Obține rutele de la un aeroport"""
        cached = cache_manager.get('airports', 'routes', dep_iata)
        if cached:
            return cached
        
        url = f"{self.base_url}/routes"
        params = {
            'api_key': self.config.key,
            'dep_iata': dep_iata.upper()
        }
        
        try:
            data = self._make_request('GET', url, params=params)
            routes = data.get('response', [])
            
            cache_manager.set('airports', routes, 'routes', dep_iata)
            return routes
            
        except APIError as e:
            st.error(f"AirLabs API Error: {e.message}")
            return []


class AeroDataBoxAPI(BaseAPI):
    """Client pentru AeroDataBox API (via RapidAPI)"""
    
    def __init__(self):
        super().__init__('rapidapi')
        keys = Settings.get_api_keys()
        self.api_key = keys['rapidapi_key']
        self.base_url = "https://aerodatabox.p.rapidapi.com"
        self.session.headers.update({
            'x-rapidapi-host': 'aerodatabox.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        })
    
    def get_airport_info(self, iata_code: str) -> Optional[dict]:
        """Obține informații despre un aeroport"""
        cached = cache_manager.get('airports', 'info', iata_code)
        if cached:
            return cached
        
        url = f"{self.base_url}/airports/iata/{iata_code.upper()}"
        
        try:
            data = self._make_request('GET', url)
            cache_manager.set('airports', data, 'info', iata_code)
            return data
            
        except APIError:
            return None
    
    def get_airport_flights(
        self, 
        iata_code: str, 
        direction: str = 'Departure',
        hours_from_now: int = 12
    ) -> List[dict]:
        """Obține zborurile de la/către un aeroport"""
        url = f"{self.base_url}/flights/airports/iata/{iata_code.upper()}/{direction}"
        
        from_time = datetime.utcnow()
        to_time = from_time + timedelta(hours=hours_from_now)
        
        params = {
            'fromLocal': from_time.strftime('%Y-%m-%dT%H:%M'),
            'toLocal': to_time.strftime('%Y-%m-%dT%H:%M')
        }
        
        try:
            data = self._make_request('GET', url, params=params)
            return data.get('departures', []) if direction == 'Departure' else data.get('arrivals', [])
        except APIError:
            return []


class FlightSearchService:
    """Serviciu principal pentru căutarea zborurilor"""
    
    def __init__(self):
        self.amadeus = AmadeusAPI()
        self.airlabs = AirLabsAPI()
        self.aerodatabox = AeroDataBoxAPI()
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
        """
        Caută zboruri din toate sursele disponibile
        """
        all_offers = []
        errors = []
        
        # Căutare Amadeus
        try:
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
        except Exception as e:
            errors.append(f"Amadeus: {str(e)}")
        
        # Sortare rezultate
        if sort_by == 'price':
            all_offers.sort(key=lambda x: x.price)
        elif sort_by == 'duration':
            all_offers.sort(key=lambda x: x.departure_time)
        elif sort_by == 'departure':
            all_offers.sort(key=lambda x: x.departure_time)
        elif sort_by == 'stops':
            all_offers.sort(key=lambda x: (x.stops, x.price))
        
        # Filtrare doar zboruri directe dacă e cerut
        if non_stop:
            all_offers = [o for o in all_offers if o.stops == 0]
        
        # Actualizează monitorul de prețuri
        if all_offers:
            route_key = f"{origin}-{destination}-{departure_date}"
            min_price = min(o.price for o in all_offers)
            cache_manager.update_price_history(route_key, min_price)
        
        return all_offers[:max_results]
    
    def get_all_airports(self) -> Dict[str, Dict[str, List[dict]]]:
        """
        Obține toate aeroporturile organizate pe continente și țări
        """
        if self._airports_cache:
            return self._airports_cache
        
        # Mapping continente
        continent_mapping = {
            'AF': 'Africa',
            'AN': 'Antarctica',
            'AS': 'Asia',
            'EU': 'Europe',
            'NA': 'North America',
            'OC': 'Oceania',
            'SA': 'South America'
        }
        
        # Inițializare structură
        organized = {cont: {} for cont in continent_mapping.values()}
        
        try:
            airports = self.airlabs.get_airports()
            
            for airport in airports:
                if not airport.get('iata_code'):
                    continue
                
                country = airport.get('country_code', 'Unknown')
                country_name = airport.get('country_name', country)
                continent_code = self._get_continent(country)
                continent_name = continent_mapping.get(continent_code, 'Other')
                
                if continent_name not in organized:
                    organized[continent_name] = {}
                
                if country_name not in organized[continent_name]:
                    organized[continent_name][country_name] = []
                
                organized[continent_name][country_name].append({
                    'iata': airport.get('iata_code'),
                    'name': airport.get('name', ''),
                    'city': airport.get('city', ''),
                    'lat': airport.get('lat'),
                    'lng': airport.get('lng')
                })
            
            # Sortare
            for continent in organized:
                organized[continent] = dict(sorted(organized[continent].items()))
                for country in organized[continent]:
                    organized[continent][country].sort(key=lambda x: x['name'])
            
            self._airports_cache = organized
            return organized
            
        except Exception as e:
            st.error(f"Error loading airports: {e}")
            return {}
    
    def _get_continent(self, country_code: str) -> str:
        """Obține codul continentului pentru o țară"""
        try:
            import pycountry_convert as pc
            return pc.country_alpha2_to_continent_code(country_code)
        except:
            # Fallback mapping pentru țările comune
            europe = ['RO', 'DE', 'FR', 'IT', 'ES', 'GB', 'NL', 'BE', 'AT', 'CH', 
                     'PL', 'CZ', 'HU', 'GR', 'PT', 'SE', 'NO', 'DK', 'FI', 'IE']
            asia = ['CN', 'JP', 'KR', 'IN', 'TH', 'VN', 'SG', 'MY', 'ID', 'PH']
            north_america = ['US', 'CA', 'MX']
            south_america = ['BR', 'AR', 'CL', 'CO', 'PE']
            africa = ['ZA', 'EG', 'MA', 'KE', 'NG']
            oceania = ['AU', 'NZ']
            
            if country_code in europe:
                return 'EU'
            elif country_code in asia:
                return 'AS'
            elif country_code in north_america:
                return 'NA'
            elif country_code in south_america:
                return 'SA'
            elif country_code in africa:
                return 'AF'
            elif country_code in oceania:
                return 'OC'
            return 'EU'  # Default
    
    def get_airport_search_list(self) -> List[tuple]:
        """Returnează lista de aeroporturi pentru selectare"""
        airports = self.get_all_airports()
        result = []
        
        for continent, countries in airports.items():
            for country, airport_list in countries.items():
                for airport in airport_list:
                    label = f"{airport['iata']} - {airport['name']} ({airport['city']}, {country})"
                    result.append((airport['iata'], label, continent, country))
        
        return sorted(result, key=lambda x: x[1])
    
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
