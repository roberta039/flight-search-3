"""
Flight Search Application - Caută cele mai ieftine zboruri
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List
import time

# Importuri locale
from services.flight_apis import FlightSearchService, FlightOffer
from services.cache_manager import cache_manager
from utils.validators import validate_search_params
from utils.helpers import format_price, format_duration, get_stops_description
from config.settings import Settings

# Configurare pagină
st.set_page_config(
    page_title="✈️ Flight Search - Găsește Zboruri Ieftine",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizat
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .flight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
    }
    .price-highlight {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4CAF50;
    }
    .direct-badge {
        background-color: #4CAF50;
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .stops-badge {
        background-color: #FF9800;
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .stDataFrame {
        font-size: 14px;
    }
    div[data-testid="stDataFrame"] > div {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inițializează session state"""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_airports' not in st.session_state:
        st.session_state.selected_airports = {}
    if 'monitored_routes' not in st.session_state:
        st.session_state.monitored_routes = {}
    if 'last_search' not in st.session_state:
        st.session_state.last_search = None
    if 'flight_service' not in st.session_state:
        st.session_state.flight_service = FlightSearchService()


def load_airports():
    """Încarcă lista de aeroporturi"""
    service = st.session_state.flight_service
    return service.get_airport_search_list()


@st.cache_data(ttl=86400)
def get_airports_by_continent():
    """Obține aeroporturile organizate pe continente"""
    service = FlightSearchService()
    return service.get_all_airports()


def create_airport_selector(label: str, key: str) -> Optional[str]:
    """Creează un selector de aeroport organizat pe continente"""
    
    airports = get_airports_by_continent()
    
    if not airports:
        st.warning("Nu s-au putut încărca aeroporturile. Introdu codul IATA manual.")
        return st.text_input(label, key=key, max_chars=3).upper()
    
    # Selectare continent
    continents = list(airports.keys())
    selected_continent = st.selectbox(
        f"🌍 Continent ({label})",
        options=continents,
        key=f"{key}_continent"
    )
    
    if selected_continent and selected_continent in airports:
        # Selectare țară
        countries = list(airports[selected_continent].keys())
        selected_country = st.selectbox(
            f"🏳️ Țară ({label})",
            options=countries,
            key=f"{key}_country"
        )
        
        if selected_country and selected_country in airports[selected_continent]:
            # Selectare aeroport
            airport_list = airports[selected_continent][selected_country]
            airport_options = [
                f"{a['iata']} - {a['name']} ({a['city']})"
                for a in airport_list
            ]
            
            if airport_options:
                selected = st.selectbox(
                    f"🛫 {label}",
                    options=airport_options,
                    key=f"{key}_airport"
                )
                
                if selected:
                    return selected.split(' - ')[0]
    
    return None


def display_flight_results(offers: List[FlightOffer], currency: str = 'EUR'):
    """Afișează rezultatele căutării într-un tabel"""
    
    if not offers:
        st.info("Nu s-au găsit zboruri pentru criteriile selectate.")
        return
    
    # Creare DataFrame
    data = [offer.to_dict() for offer in offers]
    df = pd.DataFrame(data)
    
    # Statistici
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔢 Rezultate", len(offers))
    with col2:
        min_price = df['Preț'].min()
        st.metric("💰 Cel mai ieftin", format_price(min_price, currency))
    with col3:
        avg_price = df['Preț'].mean()
        st.metric("📊 Preț mediu", format_price(avg_price, currency))
    with col4:
        direct_count = len(df[df['Escale'] == 0])
        st.metric("✈️ Zboruri directe", direct_count)
    
    st.markdown("---")
    
    # Opțiuni de afișare
    col1, col2 = st.columns([3, 1])
    with col1:
        view_mode = st.radio(
            "Mod afișare:",
            ["📊 Tabel Excel", "🎴 Carduri"],
            horizontal=True
        )
    with col2:
        sort_by = st.selectbox(
            "Sortează după:",
            ["Preț", "Durată", "Plecare", "Escale"]
        )
    
    # Sortare
    sort_mapping = {
        "Preț": "Preț",
        "Durată": "Durată",
        "Plecare": "Plecare",
        "Escale": "Escale"
    }
    df_sorted = df.sort_values(by=sort_mapping[sort_by])
    
    if "Tabel" in view_mode:
        # Afișare tabel stil Excel
        st.markdown("### 📋 Rezultate Căutare")
        
        # Configurare stiluri pentru DataFrame
        def highlight_price(val):
            if val == df['Preț'].min():
                return 'background-color: #90EE90'
            return ''
        
        def highlight_direct(val):
            if val == 0:
                return 'background-color: #90EE90'
            return ''
        
        # Afișare cu styling
        styled_df = df_sorted.style\
            .applymap(highlight_price, subset=['Preț'])\
            .applymap(highlight_direct, subset=['Escale'])\
            .format({
                'Preț': lambda x: format_price(x, currency)
            })
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=500,
            column_config={
                "Preț": st.column_config.NumberColumn(
                    "💰 Preț",
                    format="%.2f"
                ),
                "Escale": st.column_config.NumberColumn(
                    "🔄 Escale",
                    format="%d"
                ),
                "Companie": st.column_config.TextColumn(
                    "✈️ Companie",
                    width="medium"
                )
            }
        )
        
        # Buton export
        csv = df_sorted.to_csv(index=False)
        st.download_button(
            label="📥 Descarcă CSV",
            data=csv,
            file_name=f"zboruri_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    else:
        # Afișare carduri
        st.markdown("### ✈️ Zboruri Găsite")
        
        for i, offer in enumerate(offers[:20]):  # Limită 20 pentru performanță
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{offer.airline}** ({offer.airline_code})")
                    st.caption(f"🛫 {offer.origin} → 🛬 {offer.destination}")
                
                with col2:
                    st.markdown(f"**{offer.departure_time.strftime('%H:%M')}** → **{offer.arrival_time.strftime('%H:%M')}**")
                    st.caption(f"⏱️ {offer.duration}")
                
                with col3:
                    if offer.stops == 0:
                        st.success("✈️ Direct")
                    else:
                        st.warning(f"🔄 {offer.stops} {'escală' if offer.stops == 1 else 'escale'}")
                
                with col4:
                    st.markdown(f"### {format_price(offer.price, currency)}")
                    if offer.seats_available:
                        st.caption(f"🪑 {offer.seats_available} locuri")
                
                st.markdown("---")


def render_search_form():
    """Randează formularul de căutare"""
    
    st.markdown('<p class="main-header">✈️ Caută Zboruri Ieftine</p>', unsafe_allow_html=True)
    
    with st.form("search_form"):
        # Rând 1: Origine și Destinație
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🛫 De unde?")
            origin = create_airport_selector("Aeroport plecare", "origin")
        
        with col2:
            st.markdown("### 🛬 Unde?")
            destination = create_airport_selector("Aeroport sosire", "destination")
        
        st.markdown("---")
        
        # Rând 2: Date
        col1, col2 = st.columns(2)
        
        with col1:
            departure_date = st.date_input(
                "📅 Data plecării",
                min_value=date.today(),
                max_value=date.today() + timedelta(days=365),
                value=date.today() + timedelta(days=30)
            )
        
        with col2:
            trip_type = st.radio(
                "Tip călătorie",
                ["Doar dus", "Dus-întors"],
                horizontal=True
            )
            
            return_date = None
            if trip_type == "Dus-întors":
                return_date = st.date_input(
                    "📅 Data întoarcerii",
                    min_value=departure_date,
                    max_value=date.today() + timedelta(days=365),
                    value=departure_date + timedelta(days=7)
                )
        
        st.markdown("---")
        
        # Rând 3: Pasageri și Opțiuni
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            adults = st.number_input("👨 Adulți", min_value=1, max_value=9, value=1)
        
        with col2:
            children = st.number_input("👶 Copii (2-11)", min_value=0, max_value=8, value=0)
        
        with col3:
            infants = st.number_input("🍼 Bebeluși (<2)", min_value=0, max_value=adults, value=0)
        
        with col4:
            cabin_class = st.selectbox(
                "💺 Clasă",
                options=list(Settings.CABIN_CLASSES.keys()),
                format_func=lambda x: Settings.CABIN_CLASSES[x]
            )
        
        # Rând 4: Opțiuni suplimentare
        col1, col2, col3 = st.columns(3)
        
        with col1:
            non_stop = st.checkbox("✈️ Doar zboruri directe", value=False)
        
        with col2:
            currency = st.selectbox(
                "💱 Monedă",
                options=['EUR', 'USD', 'GBP', 'RON'],
                index=0
            )
        
        with col3:
            max_results = st.slider(
                "📊 Max rezultate",
                min_value=10,
                max_value=100,
                value=50
            )
        
        # Buton căutare
        submitted = st.form_submit_button(
            "🔍 Caută Zboruri",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            return {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date.strftime('%Y-%m-%d') if departure_date else None,
                'return_date': return_date.strftime('%Y-%m-%d') if return_date else None,
                'adults': adults,
                'children': children,
                'infants': infants,
                'cabin_class': cabin_class,
                'non_stop': non_stop,
                'currency': currency,
                'max_results': max_results
            }
    
    return None


def render_price_monitor():
    """Randează secțiunea de monitorizare prețuri"""
    
    st.markdown("### 📈 Monitor Prețuri")
    
    monitors = cache_manager.get_price_monitors()
    
    if not monitors:
        st.info("Nu ai nicio rută monitorizată. Caută un zbor și adaugă-l la monitorizare!")
        return
    
    for route_key, monitor in monitors.items():
        with st.expander(f"🛫 {route_key}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Preț minim găsit",
                    format_price(monitor['lowest_price'] or 0, 'EUR')
                )
            
            with col2:
                target = monitor.get('target_price')
                if target:
                    st.metric("Preț țintă", format_price(target, 'EUR'))
                else:
                    st.caption("Fără preț țintă setat")
            
            with col3:
                last_check = monitor.get('last_check')
                if last_check:
                    st.caption(f"Ultima verificare: {last_check.strftime('%H:%M')}")
            
            # Istoric prețuri
            history = cache_manager.get_price_history(route_key)
            if history:
                import altair as alt
                
                df = pd.DataFrame(history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                chart = alt.Chart(df).mark_line(point=True).encode(
                    x='timestamp:T',
                    y='price:Q',
                    tooltip=['timestamp:T', 'price:Q']
                ).properties(height=200)
                
                st.altair_chart(chart, use_container_width=True)
            
            if st.button(f"🗑️ Elimină", key=f"remove_{route_key}"):
                cache_manager.remove_price_monitor(route_key)
                st.rerun()


def render_sidebar():
    """Randează sidebar-ul"""
    
    with st.sidebar:
        st.markdown("## ⚙️ Setări")
        
        # Status API-uri
        st.markdown("### 📡 Status API-uri")
        
        keys = Settings.get_api_keys()
        
        api_status = {
            "Amadeus": bool(keys['amadeus_key'] and keys['amadeus_secret']),
            "AirLabs": bool(keys['airlabs_key']),
            "RapidAPI": bool(keys['rapidapi_key'])
        }
        
        for api, status in api_status.items():
            if status:
                st.success(f"✅ {api}")
            else:
                st.error(f"❌ {api}")
        
        st.markdown("---")
        
        # Auto-refresh
        st.markdown("### 🔄 Auto-refresh")
        
        auto_refresh = st.checkbox("Activează auto-refresh", value=False)
        
        if auto_refresh:
            refresh_interval = st.slider(
                "Interval (minute)",
                min_value=5,
                max_value=60,
                value=15
            )
            
            st.info(f"Se va reîmprospăta la fiecare {refresh_interval} minute")
            
            # Implementare auto-refresh folosind streamlit-autorefresh
            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=refresh_interval * 60 * 1000, key="auto_refresh")
            except ImportError:
                st.warning("Instalează streamlit-autorefresh pentru auto-refresh")
        
        st.markdown("---")
        
        # Despre
        st.markdown("### ℹ️ Despre")
        st.caption("""
        **Flight Search App**
        
        Caută cele mai ieftine zboruri 
        din multiple surse.
        
        Folosește API-uri oficiale:
        - Amadeus
        - AirLabs
        - AeroDataBox
        
        © 2024
        """)
        
        # Clear cache
        if st.button("🗑️ Golește Cache"):
            cache_manager.clear_cache()
            st.success("Cache-ul a fost golit!")
            st.rerun()


def main():
    """Funcția principală"""
    
    # Inițializare
    init_session_state()
    
    # Sidebar
    render_sidebar()
    
    # Tabs principale
    tab1, tab2, tab3 = st.tabs([
        "🔍 Căutare Zboruri",
        "📈 Monitor Prețuri",
        "🌍 Explorează Aeroporturi"
    ])
    
    with tab1:
        # Formular căutare
        search_params = render_search_form()
        
        if search_params:
            # Validare
            is_valid, errors = validate_search_params(
                origin=search_params['origin'] or '',
                destination=search_params['destination'] or '',
                departure_date=search_params['departure_date'] or '',
                return_date=search_params['return_date'],
                adults=search_params['adults'],
                children=search_params['children'],
                infants=search_params['infants']
            )
            
            if not is_valid:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Căutare
                with st.spinner("🔍 Căutare în curs..."):
                    service = st.session_state.flight_service
                    
                    results = service.search_flights(
                        origin=search_params['origin'],
                        destination=search_params['destination'],
                        departure_date=search_params['departure_date'],
                        return_date=search_params['return_date'],
                        adults=search_params['adults'],
                        children=search_params['children'],
                        infants=search_params['infants'],
                        cabin_class=search_params['cabin_class'],
                        non_stop=search_params['non_stop'],
                        currency=search_params['currency'],
                        max_results=search_params['max_results']
                    )
                    
                    st.session_state.search_results = results
                    st.session_state.last_search = search_params
        
        # Afișare rezultate
        if st.session_state.search_results:
            st.markdown("---")
            
            # Buton adăugare la monitor
            if st.session_state.last_search:
                col1, col2 = st.columns([3, 1])
                with col2:
                    target_price = st.number_input(
                        "💰 Preț țintă (opțional
