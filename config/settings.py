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
    rate_limit: int = 100
    enabled: bool = True


class Settings:
    """Manager central pentru configurări"""
    
    # Rate limiting defaults (requests per minute)
    RATE_LIMITS = {
        'rapidapi': 5,
        'airlabs': 10,
        'tequila': 10,
        'travelpayouts': 10
    }
    
    # Cache TTL (time to live) în secunde
    CACHE_TTL = {
        'airports': 86400,      # 24 ore
        'flights': 300,         # 5 minute
        'prices': 180           # 3 minute
    }
    
    # Cabin classes disponibile
    CABIN_CLASSES = {
        'M': 'Economy',
        'W': 'Premium Economy', 
        'C': 'Business',
        'F': 'First Class'
    }
    
    @classmethod
    def get_api_keys(cls) -> dict:
        """Obține cheile API din Streamlit secrets sau environment"""
        try:
            # Încearcă Streamlit secrets (pentru deployment)
            return {
                'rapidapi_key': st.secrets.get("RAPIDAPI_KEY", ""),
                'airlabs_key': st.secrets.get("AIRLABS_API_KEY", ""),
                'tequila_key': st.secrets.get("TEQUILA_API_KEY", ""),
            }
        except Exception:
            # Fallback pentru environment variables
            return {
                'rapidapi_key': os.getenv("RAPIDAPI_KEY", ""),
                'airlabs_key': os.getenv("AIRLABS_API_KEY", ""),
                'tequila_key': os.getenv("TEQUILA_API_KEY", ""),
            }
    
    @classmethod
    def get_rapidapi_config(cls) -> APIConfig:
        """Configurare RapidAPI"""
        keys = cls.get_api_keys()
        return APIConfig(
            name="RapidAPI",
            base_url="https://sky-scrapper.p.rapidapi.com",
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
    
    @classmethod
    def get_tequila_config(cls) -> APIConfig:
        """Configurare Kiwi Tequila API"""
        keys = cls.get_api_keys()
        return APIConfig(
            name="Tequila",
            base_url="https://api.tequila.kiwi.com",
            key=keys['tequila_key'],
            rate_limit=cls.RATE_LIMITS['tequila']
        )
