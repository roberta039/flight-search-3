"""Configuration settings for the flight search application."""
import streamlit as st
from typing import Dict, Any

class APIConfig:
    """API Configuration Manager"""
    
    @staticmethod
    def get_rapidapi_key() -> str:
        """Get RapidAPI key from Streamlit secrets"""
        try:
            return st.secrets['rapidapi']['key']
        except Exception:
            return '5a26e14d6amsheeb99b61b3ff65ep17583cjsn4eb17402fec4'
    
    @staticmethod
    def get_airlabs_key() -> str:
        """Get AirLabs API key"""
        try:
            return st.secrets['airlabs']['api_key']
        except Exception:
            return '15151c68-6858-4cc2-a819-33b87bfc7651'

class AppConfig:
    """Application Configuration"""
    
    # Rate limiting settings (requests per minute)
    RATE_LIMITS = {
        'rapidapi': 5,
        'airlabs': 10,
        'skyscanner': 5
    }
    
    # Cache settings (in seconds)
    CACHE_TTL = {
        'flight_search': 300,  # 5 minutes
        'airport_data': 3600,  # 1 hour
        'price_monitor': 900   # 15 minutes
    }
    
    # Supported cabin classes
    CABIN_CLASSES = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST']
    
    # Maximum number of results
    MAX_RESULTS = 50
    
    # Auto-refresh intervals (in seconds)
    REFRESH_INTERVALS = {
        '5 minutes': 300,
        '15 minutes': 900,
        '30 minutes': 1800,
        '1 hour': 3600
    }
