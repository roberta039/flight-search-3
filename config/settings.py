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
    rate_limit: int = 100
    enabled: bool = True


class Settings:
    """Manager central pentru configurări"""
    
    RATE_LIMITS = {
        'rapidapi': 5,
        'airlabs': 10,
    }
    
    CACHE_TTL = {
        'airports': 86400,
        'flights': 300,
        'prices': 180
    }
    
    CABIN_CLASSES = {
        'economy': 'Economy',
        'premium_economy': 'Premium Economy',
        'business': 'Business',
        'first': 'First Class'
    }
    
    @classmethod
    def get_api_keys(cls) -> dict:
        """Obține cheile API din Streamlit secrets"""
        try:
            return {
                'rapidapi_key': st.secrets.get("RAPIDAPI_KEY", ""),
                'airlabs_key': st.secrets.get("AIRLABS_API_KEY", ""),
            }
        except Exception:
            return {
                'rapidapi_key': os.getenv("RAPIDAPI_KEY", ""),
                'airlabs_key': os.getenv("AIRLABS_API_KEY", ""),
            }
    
    @classmethod
    def get_rapidapi_config(cls) -> APIConfig:
        keys = cls.get_api_keys()
        return APIConfig(
            name="RapidAPI",
            base_url="https://sky-scrapper.p.rapidapi.com",
            key=keys['rapidapi_key'],
            rate_limit=cls.RATE_LIMITS['rapidapi']
        )
    
    @classmethod
    def get_airlabs_config(cls) -> APIConfig:
        keys = cls.get_api_keys()
        return APIConfig(
            name="AirLabs",
            base_url="https://airlabs.co/api/v9",
            key=keys['airlabs_key'],
            rate_limit=cls.RATE_LIMITS['airlabs']
        )
