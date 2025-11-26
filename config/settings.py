"""
Configurări centrale pentru aplicația de căutare zboruri
"""
import streamlit as st
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class APIConfig:
    """Configurare pentru un API"""
    name: str
    base_url: str
    key: str
    secret: Optional[str] = None
    rate_limit: int = 100  # requests per minute
    enabled: bool = True


class Settings:
    """Manager central pentru configurări"""
    
    # Rate limiting defaults (requests per minute)
    RATE_LIMITS = {
        'amadeus': 10,
        'rapidapi': 5,
        'airlabs': 10,
        'aviationstack': 5
    }
    
    # Cache TTL (time to live) în secunde
    CACHE_TTL = {
        'airports': 86400,      # 24 ore
        'flights': 300,         # 5 minute
        'prices': 180           # 3 minute
    }
    
    # Cabin classes disponibile
    CABIN_CLASSES = {
        'ECONOMY': 'Economy',
        'PREMIUM_ECONOMY': 'Premium Economy',
        'BUSINESS': 'Business',
        'FIRST': 'First Class'
    }
    
    @classmethod
    def get_api_keys(cls) -> dict:
        """Obține cheile API din Streamlit secrets sau environment"""
        try:
            # Încearcă Streamlit secrets (pentru deployment)
            return {
                'rapidapi_key': st.secrets.get("RAPIDAPI_KEY", ""),
                'amadeus_key': st.secrets.get("AMADEUS_API_KEY", ""),
                'amadeus_secret': st.secrets.get("AMADEUS_API_SECRET", ""),
                'airlabs_key': st.secrets.get("AIRLABS_API_KEY", ""),
                'aerodatabox_key': st.secrets.get("AERODATABOX_KEY", "")
            }
        except Exception:
            # Fallback pentru environment variables
            return {
                'rapidapi_key': os.getenv("RAPIDAPI_KEY", ""),
                'amadeus_key': os.getenv("AMADEUS_API_KEY", ""),
                'amadeus_secret': os.getenv("AMADEUS_API_SECRET", ""),
                'airlabs_key': os.getenv("AIRLABS_API_KEY", ""),
                'aerodatabox_key': os.getenv("AERODATABOX_KEY", "")
            }
    
    @classmethod
    def get_amadeus_config(cls) -> APIConfig:
        """Configurare Amadeus API"""
        keys = cls.get_api_keys()
        return APIConfig(
            name="Amadeus",
            base_url="https://api.amadeus.com",
            key=keys['amadeus_key'],
            secret=keys['amadeus_secret'],
            rate_limit=cls.RATE_LIMITS['amadeus']
        )
    
    @classmethod
    def get_rapidapi_config(cls) -> APIConfig:
        """Configurare RapidAPI"""
        keys = cls.get_api_keys()
        return APIConfig(
            name="RapidAPI",
            base_url="https://rapidapi.com",
            key=keys['rapidapi_key'],
            rate_limit=cls.RATE_LIMITS['rapidapi']
        )
    
    @classmethod
    def get_airlabs_config(cls) -> APIConfig:
        """Configurare AirLabs API"""
        keys = cls.get_api_keys()
        return APIConfig(
            name="AirLabs",
            base_url="https://airlabs.co/api/v9",
            key=keys['airlabs_key'],
            rate_limit=cls.RATE_LIMITS['airlabs']
        )
