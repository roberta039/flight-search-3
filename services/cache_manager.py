"""
Manager pentru cache și rate limiting
"""
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from cachetools import TTLCache
from collections import defaultdict
import threading


class RateLimiter:
    """Rate limiter pentru API calls"""
    
    def __init__(self, max_calls: int, period: int = 60):
        """
        Args:
            max_calls: Numărul maxim de apeluri
            period: Perioada în secunde
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()
    
    def can_call(self) -> bool:
        """Verifică dacă poate face un apel"""
        with self.lock:
            now = time.time()
            # Elimină apelurile vechi
            self.calls = [t for t in self.calls if now - t < self.period]
            return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Înregistrează un apel"""
        with self.lock:
            self.calls.append(time.time())
    
    def wait_time(self) -> float:
        """Returnează timpul de așteptare până la următorul apel disponibil"""
        with self.lock:
            if len(self.calls) < self.max_calls:
                return 0
            oldest = min(self.calls)
            return max(0, self.period - (time.time() - oldest))
    
    def __call__(self, func):
        """Decorator pentru rate limiting"""
        def wrapper(*args, **kwargs):
            wait = self.wait_time()
            if wait > 0:
                time.sleep(wait)
            self.record_call()
            return func(*args, **kwargs)
        return wrapper


class CacheManager:
    """Manager central pentru cache"""
    
    def __init__(self):
        # Cache-uri separate pentru diferite tipuri de date
        self._caches: Dict[str, TTLCache] = {
            'airports': TTLCache(maxsize=10000, ttl=86400),  # 24h
            'flights': TTLCache(maxsize=1000, ttl=300),       # 5min
            'prices': TTLCache(maxsize=500, ttl=180),         # 3min
            'token': TTLCache(maxsize=10, ttl=1700)           # ~28min pentru Amadeus token
        }
        
        # Rate limiters pentru fiecare API
        self._rate_limiters: Dict[str, RateLimiter] = {
            'amadeus': RateLimiter(max_calls=10, period=60),
            'rapidapi': RateLimiter(max_calls=5, period=60),
            'airlabs': RateLimiter(max_calls=10, period=60),
            'aviationstack': RateLimiter(max_calls=5, period=60)
        }
        
        # Monitorizare prețuri
        self._price_monitors: Dict[str, dict] = {}
        self._price_history: Dict[str, list] = defaultdict(list)
    
    @staticmethod
    def _generate_key(*args) -> str:
        """Generează o cheie unică pentru cache"""
        key_str = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, cache_type: str, *key_parts) -> Optional[Any]:
        """Obține valoare din cache"""
        if cache_type not in self._caches:
            return None
        key = self._generate_key(*key_parts)
        return self._caches[cache_type].get(key)
    
    def set(self, cache_type: str, value: Any, *key_parts):
        """Setează valoare în cache"""
        if cache_type not in self._caches:
            return
        key = self._generate_key(*key_parts)
        self._caches[cache_type][key] = value
    
    def get_rate_limiter(self, api_name: str) -> RateLimiter:
        """Obține rate limiter pentru un API"""
        if api_name not in self._rate_limiters:
            self._rate_limiters[api_name] = RateLimiter(max_calls=10, period=60)
        return self._rate_limiters[api_name]
    
    def can_call_api(self, api_name: str) -> bool:
        """Verifică dacă poate apela un API"""
        return self.get_rate_limiter(api_name).can_call()
    
    def record_api_call(self, api_name: str):
        """Înregistrează un apel API"""
        self.get_rate_limiter(api_name).record_call()
    
    # Monitorizare prețuri
    def add_price_monitor(self, route_key: str, search_params: dict, 
                          target_price: Optional[float] = None):
        """Adaugă un monitor de prețuri pentru o rută"""
        self._price_monitors[route_key] = {
            'params': search_params,
            'target_price': target_price,
            'created_at': datetime.now(),
            'last_check': None,
            'lowest_price': None
        }
    
    def remove_price_monitor(self, route_key: str):
        """Elimină un monitor de prețuri"""
        if route_key in self._price_monitors:
            del self._price_monitors[route_key]
    
    def update_price_history(self, route_key: str, price: float):
        """Actualizează istoricul prețurilor"""
        self._price_history[route_key].append({
            'price': price,
            'timestamp': datetime.now()
        })
        # Păstrează doar ultimele 100 de înregistrări
        if len(self._price_history[route_key]) > 100:
            self._price_history[route_key] = self._price_history[route_key][-100:]
        
        # Actualizează monitorul
        if route_key in self._price_monitors:
            monitor = self._price_monitors[route_key]
            monitor['last_check'] = datetime.now()
            if monitor['lowest_price'] is None or price < monitor['lowest_price']:
                monitor['lowest_price'] = price
    
    def get_price_monitors(self) -> Dict[str, dict]:
        """Returnează toate monitoarele de prețuri"""
        return self._price_monitors.copy()
    
    def get_price_history(self, route_key: str) -> list:
        """Returnează istoricul prețurilor pentru o rută"""
        return self._price_history.get(route_key, [])
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """Golește cache-ul"""
        if cache_type:
            if cache_type in self._caches:
                self._caches[cache_type].clear()
        else:
            for cache in self._caches.values():
                cache.clear()


# Instanță globală
cache_manager = CacheManager()
