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
    .airport-selector {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inițializează session state"""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'monitored_routes' not in st.session_state:
        st.session_state.monitored_routes = {}
    if 'last_search' not in st.session_state:
        st.session_state.last_search = None
    if 'flight_service' not in st.session_state:
        st.session_state.flight_service = FlightSearchService()
    
    # Pentru selectoare
    if 'origin_continent' not in st.session_state:
        st.session_state.origin_continent = None
    if 'origin_country' not in st.session_state:
        st.session_state.origin_country = None
    if 'origin_airport' not in st.session_state:
        st.session_state.origin_airport = None
    if 'dest_continent' not in st.session_state:
        st.session_state.dest_continent = None
    if 'dest_country' not in st.session_state:
        st.session_state.dest_country = None
    if 'dest_airport' not in st.session_state:
        st.session_state.dest_airport = None


@st.cache_data(ttl=86400, show_spinner=False)
def get_airports_by_continent():
    """Obține aeroporturile organizate pe continente"""
    service = FlightSearchService()
    return service.get_all_airports()


def create_airport_selector(label: str, key_prefix: str) -> Optional[str]:
    """
    Creează un selector de aeroport organizat pe continente
    FĂRĂ a fi în interiorul unui form pentru actualizare dinamică
    """
    
    airports = get_airports_by_continent()
    
    if not airports:
        st.warning("Nu s-au putut încărca aeroporturile. Introdu codul IATA manual.")
        manual_code = st.text_input(
            f"Cod IATA {label}", 
            key=f"{key_prefix}_manual",
            max_chars=3,
            placeholder="Ex: OTP"
        )
        return manual_code.upper() if manual_code else None
    
    st.markdown(f"**{label}**")
    
    # Container pentru selectoare
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Selectare continent
        continents = ["-- Selectează --"] + list(airports.keys())
        
        # Găsește indexul curent
        current_continent = st.session_state.get(f'{key_prefix}_continent', None)
        continent_index = 0
        if current_continent and current_continent in continents:
            continent_index = continents.index(current_continent)
        
        selected_continent = st.selectbox(
            "🌍 Continent",
            options=continents,
            index=continent_index,
            key=f"{key_prefix}_continent_select"
        )
        
        # Actualizează session state
        if selected_continent != "-- Selectează --":
            if st.session_state.get(f'{key_prefix}_continent') != selected_continent:
                st.session_state[f'{key_prefix}_continent'] = selected_continent
                st.session_state[f'{key_prefix}_country'] = None
                st.session_state[f'{key_prefix}_airport'] = None
    
    with col2:
        # Selectare țară
        countries = ["-- Selectează --"]
        
        if selected_continent and selected_continent != "-- Selectează --":
            if selected_continent in airports:
                countries = ["-- Selectează --"] + sorted(list(airports[selected_continent].keys()))
        
        # Găsește indexul curent
        current_country = st.session_state.get(f'{key_prefix}_country', None)
        country_index = 0
        if current_country and current_country in countries:
            country_index = countries.index(current_country)
        
        selected_country = st.selectbox(
            "🏳️ Țară",
            options=countries,
            index=country_index,
            key=f"{key_prefix}_country_select"
        )
        
        # Actualizează session state
        if selected_country != "-- Selectează --":
            if st.session_state.get(f'{key_prefix}_country') != selected_country:
                st.session_state[f'{key_prefix}_country'] = selected_country
                st.session_state[f'{key_prefix}_airport'] = None
    
    with col3:
        # Selectare aeroport
        airport_options = ["-- Selectează --"]
        airport_codes = {}
        
        if (selected_continent and selected_continent != "-- Selectează --" and
            selected_country and selected_country != "-- Selectează --"):
            
            if selected_continent in airports and selected_country in airports[selected_continent]:
                airport_list = airports[selected_continent][selected_country]
                for a in airport_list:
                    display_name = f"{a['iata']} - {a['name']}"
                    if a.get('city'):
                        display_name += f" ({a['city']})"
                    airport_options.append(display_name)
                    airport_codes[display_name] = a['iata']
        
        # Găsește indexul curent
        current_airport = st.session_state.get(f'{key_prefix}_airport', None)
        airport_index = 0
        if current_airport:
            for i, opt in enumerate(airport_options):
                if opt.startswith(current_airport):
                    airport_index = i
                    break
        
        selected_airport_display = st.selectbox(
            "✈️ Aeroport",
            options=airport_options,
            index=airport_index,
            key=f"{key_prefix}_airport_select"
        )
        
        # Extrage codul IATA
        selected_airport = None
        if selected_airport_display and selected_airport_display != "-- Selectează --":
            selected_airport = airport_codes.get(selected_airport_display)
            if selected_airport:
                st.session_state[f'{key_prefix}_airport'] = selected_airport
    
    return selected_airport


def display_flight_results(offers: List[FlightOffer], currency: str = 'EUR'):
    """Afișează rezultatele căutării într-un tabel"""
    
    if not offers:
        st.info("🔍 Nu s-au găsit zboruri pentru criteriile selectate. Încearcă alte date sau dezactivează filtrul 'Doar zboruri directe'.")
        return
    
    # Creare DataFrame
    data = [offer.to_dict() for offer in offers]
    df = pd.DataFrame(data)
    
    # Statistici
    st.markdown("### 📊 Rezumat")
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
    
    # Opțiuni de afișare și filtrare
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        view_mode = st.radio(
            "Mod afișare:",
            ["📊 Tabel Excel", "🎴 Carduri"],
            horizontal=True,
            key="view_mode"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sortează după:",
            ["Preț (crescător)", "Preț (descrescător)", "Durată", "Ora plecării", "Escale"],
            key="sort_by"
        )
    
    with col3:
        filter_direct = st.checkbox("Arată doar zboruri directe", key="filter_direct_results")
    
    # Filtrare
    df_filtered = df.copy()
    if filter_direct:
        df_filtered = df_filtered[df_filtered['Escale'] == 0]
    
    # Sortare
    if sort_by == "Preț (crescător)":
        df_filtered = df_filtered.sort_values(by='Preț', ascending=True)
    elif sort_by == "Preț (descrescător)":
        df_filtered = df_filtered.sort_values(by='Preț', ascending=False)
    elif sort_by == "Durată":
        df_filtered = df_filtered.sort_values(by='Durată')
    elif sort_by == "Ora plecării":
        df_filtered = df_filtered.sort_values(by='Plecare')
    elif sort_by == "Escale":
        df_filtered = df_filtered.sort_values(by=['Escale', 'Preț'])
    
    # Filtrare oferte pentru carduri
    filtered_offers = [o for o in offers if o.id in df_filtered['ID'].values] if filter_direct else offers
    
    if "Tabel" in view_mode:
        # Afișare tabel stil Excel
        st.markdown("### 📋 Rezultate Căutare")
        
        # Selectează coloanele de afișat
        columns_to_show = ['Companie', 'Cod', 'De la', 'Către', 'Plecare', 'Sosire', 'Durată', 'Preț', 'Monedă', 'Escale', 'Locuri']
        df_display = df_filtered[columns_to_show].copy()
        
        # Afișare DataFrame
        st.dataframe(
            df_display,
            use_container_width=True,
            height=500,
            column_config={
                "Preț": st.column_config.NumberColumn(
                    "💰 Preț",
                    format="%.2f €"
                ),
                "Escale": st.column_config.NumberColumn(
                    "🔄 Escale",
                    format="%d"
                ),
                "Companie": st.column_config.TextColumn(
                    "✈️ Companie",
                    width="medium"
                ),
                "De la": st.column_config.TextColumn(
                    "🛫 De la",
                    width="small"
                ),
                "Către": st.column_config.TextColumn(
                    "🛬 Către",
                    width="small"
                ),
            },
            hide_index=True
        )
        
        # Buton export
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Descarcă CSV",
            data=csv,
            file_name=f"zboruri_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    else:
        # Afișare carduri
        st.markdown("### ✈️ Zboruri Găsite")
        
        if not filtered_offers:
            st.info("Nu există zboruri directe pentru această rută.")
            return
        
        for i, offer in enumerate(filtered_offers[:30]):  # Limită 30 pentru performanță
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{offer.airline}** ({offer.airline_code})")
                    st.caption(f"🛫 {offer.origin} → 🛬 {offer.destination}")
                
                with col2:
                    dep_time = offer.departure_time.strftime('%H:%M')
                    arr_time = offer.arrival_time.strftime('%H:%M')
                    dep_date = offer.departure_time.strftime('%d %b')
                    st.markdown(f"**{dep_time}** → **{arr_time}**")
                    st.caption(f"📅 {dep_date} | ⏱️ {offer.duration}")
                
                with col3:
                    if offer.stops == 0:
                        st.success("✈️ Direct")
                    else:
                        st.warning(f"🔄 {offer.stops} {'escală' if offer.stops == 1 else 'escale'}")
                
                with col4:
                    st.markdown(f"### {format_price(offer.price, offer.currency)}")
                    if offer.seats_available:
                        if offer.seats_available <= 3:
                            st.error(f"🪑 Doar {offer.seats_available} locuri!")
                        else:
                            st.caption(f"🪑 {offer.seats_available} locuri")
                
                st.markdown("---")


def render_search_form():
    """Randează formularul de căutare"""
    
    st.markdown('<p class="main-header">✈️ Caută Zboruri Ieftine</p>', unsafe_allow_html=True)
    
    # ============================================
    # SELECTOARE AEROPORTURI (în afara formularului)
    # ============================================
    
    st.markdown("### 🛫 Selectează Aeroporturile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### De unde pleci?")
        with st.container():
            origin = create_airport_selector("Origine", "origin")
            if origin:
                st.success(f"✅ Selectat: **{origin}**")
    
    with col2:
        st.markdown("##### Unde mergi?")
        with st.container():
            destination = create_airport_selector("Destinație", "dest")
            if destination:
                st.success(f"✅ Selectat: **{destination}**")
    
    st.markdown("---")
    
    # ============================================
    # RESTUL FORMULARULUI
    # ============================================
    
    with st.form("search_form"):
        # Rând 1: Date
        st.markdown("### 📅 Date Călătorie")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            departure_date = st.date_input(
                "Data plecării",
                min_value=date.today(),
                max_value=date.today() + timedelta(days=365),
                value=date.today() + timedelta(days=30)
            )
        
        with col2:
            trip_type = st.radio(
                "Tip călătorie",
                ["✈️ Doar dus", "🔄 Dus-întors"],
                horizontal=True
            )
        
        with col3:
            return_date = None
            if "Dus-întors" in trip_type:
                return_date = st.date_input(
                    "Data întoarcerii",
                    min_value=departure_date + timedelta(days=1),
                    max_value=date.today() + timedelta(days=365),
                    value=departure_date + timedelta(days=7)
                )
            else:
                st.empty()
        
        st.markdown("---")
        
        # Rând 2: Pasageri
        st.markdown("### 👥 Pasageri")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            adults = st.number_input("👨 Adulți (12+)", min_value=1, max_value=9, value=1)
        
        with col2:
            children = st.number_input("👶 Copii (2-11)", min_value=0, max_value=8, value=0)
        
        with col3:
            infants = st.number_input("🍼 Bebeluși (<2)", min_value=0, max_value=adults, value=0)
        
        with col4:
            cabin_class = st.selectbox(
                "💺 Clasă",
                options=['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'],
                format_func=lambda x: {
                    'ECONOMY': '💺 Economy',
                    'PREMIUM_ECONOMY': '💺 Premium Economy',
                    'BUSINESS': '💼 Business',
                    'FIRST': '👑 First Class'
                }.get(x, x)
            )
        
        st.markdown("---")
        
        # Rând 3: Opțiuni
        st.markdown("### ⚙️ Opțiuni Căutare")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            non_stop = st.checkbox("✈️ **Doar zboruri directe**", value=False)
        
        with col2:
            currency = st.selectbox(
                "💱 Monedă",
                options=['EUR', 'USD', 'GBP', 'RON'],
                index=0
            )
        
        with col3:
            max_results = st.slider(
                "📊 Număr maxim rezultate",
                min_value=10,
                max_value=100,
                value=50,
                step=10
            )
        
        st.markdown("---")
        
        # Buton căutare
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🔍 CAUTĂ ZBORURI",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Preia valorile din session state pentru aeroporturi
            final_origin = st.session_state.get('origin_airport') or origin
            final_destination = st.session_state.get('dest_airport') or destination
            
            return {
                'origin': final_origin,
                'destination': final_destination,
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
    st.caption("Urmărește evoluția prețurilor pentru rutele tale favorite")
    
    monitors = cache_manager.get_price_monitors()
    
    if not monitors:
        st.info("📭 Nu ai nicio rută monitorizată încă.\n\nCaută un zbor și apasă 'Adaugă la Monitor' pentru a urmări prețurile!")
        return
    
    for route_key, monitor in monitors.items():
        with st.expander(f"🛫 {route_key}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                lowest = monitor.get('lowest_price')
                if lowest:
                    st.metric("💰 Preț minim", format_price(lowest, 'EUR'))
                else:
                    st.metric("💰 Preț minim", "N/A")
            
            with col2:
                target = monitor.get('target_price')
                if target:
                    st.metric("🎯 Preț țintă", format_price(target, 'EUR'))
                    if lowest and lowest <= target:
                        st.success("✅ Sub prețul țintă!")
                else:
                    st.caption("Fără preț țintă")
            
            with col3:
                last_check = monitor.get('last_check')
                if last_check:
                    st.caption(f"🕐 Ultima verificare:")
                    st.caption(f"{last_check.strftime('%d/%m %H:%M')}")
            
            with col4:
                if st.button(f"🗑️ Șterge", key=f"remove_{route_key}"):
                    cache_manager.remove_price_monitor(route_key)
                    st.rerun()
            
            # Istoric prețuri
            history = cache_manager.get_price_history(route_key)
            if history and len(history) > 1:
                st.markdown("**📊 Evoluție prețuri:**")
                df = pd.DataFrame(history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                st.line_chart(df['price'])


def render_airport_explorer():
    """Randează exploratorul de aeroporturi"""
    
    st.markdown("### 🌍 Explorează Aeroporturi din Toată Lumea")
    st.caption("Descoperă toate aeroporturile organizate pe continente și țări")
    
    airports = get_airports_by_continent()
    
    if not airports:
        st.warning("⚠️ Nu s-au putut încărca aeroporturile. Verifică conexiunea API.")
        return
    
    # Statistici globale
    total_airports = sum(
        len(airports[cont][country])
        for cont in airports
        for country in airports[cont]
    )
    
    total_countries = sum(len(airports[cont]) for cont in airports)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🌍 Continente", len(airports))
    with col2:
        st.metric("🏳️ Țări", total_countries)
    with col3:
        st.metric("✈️ Aeroporturi", total_airports)
    
    st.markdown("---")
    
    # Selectare continent și țară
    col1, col2 = st.columns(2)
    
    with col1:
        selected_continent = st.selectbox(
            "🌍 Selectează Continentul",
            options=list(airports.keys()),
            key="explorer_continent"
        )
    
    selected_country = None
    with col2:
        if selected_continent:
            countries = sorted(list(airports[selected_continent].keys()))
            selected_country = st.selectbox(
                "🏳️ Selectează Țara",
                options=countries,
                key="explorer_country"
            )
    
    # Afișare aeroporturi
    if selected_continent and selected_country:
        airport_list = airports[selected_continent][selected_country]
        
        st.markdown(f"### ✈️ Aeroporturi în {selected_country}")
        st.caption(f"Total: {len(airport_list)} aeroporturi")
        
        # Creare DataFrame
        df = pd.DataFrame(airport_list)
        
        if not df.empty:
            # Redenumește coloanele
            df.columns = ['Cod IATA', 'Nume Aeroport', 'Oraș', 'Latitudine', 'Longitudine']
            
            # Afișare tabel
            st.dataframe(
                df[['Cod IATA', 'Nume Aeroport', 'Oraș']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cod IATA": st.column_config.TextColumn("🏷️ IATA", width="small"),
                    "Nume Aeroport": st.column_config.TextColumn("✈️ Aeroport", width="large"),
                    "Oraș": st.column_config.TextColumn("🏙️ Oraș", width="medium"),
                }
            )
            
            # Export
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"📥 Descarcă aeroporturi {selected_country}",
                data=csv,
                file_name=f"aeroporturi_{selected_country}.csv",
                mime="text/csv"
            )


def render_sidebar():
    """Randează sidebar-ul"""
    
    with st.sidebar:
        st.markdown("## ⚙️ Setări & Info")
        
        # Status API-uri
        st.markdown("### 📡 Status API-uri")
        
        keys = Settings.get_api_keys()
        
        api_status = {
            "Amadeus": bool(keys.get('amadeus_key') and keys.get('amadeus_secret')),
            "AirLabs": bool(keys.get('airlabs_key')),
            "RapidAPI": bool(keys.get('rapidapi_key'))
        }
        
        for api, status in api_status.items():
            if status:
                st.success(f"✅ {api} - Conectat")
            else:
                st.error(f"❌ {api} - Neconfig.")
        
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
            
            st.info(f"🔄 Refresh la fiecare {refresh_interval} min")
            
            try:
                from streamlit_autorefresh import st_autorefresh
                count = st_autorefresh(
                    interval=refresh_interval * 60 * 1000, 
                    key="auto_refresh"
                )
                if count > 0:
                    st.caption(f"Refresh #{count}")
            except ImportError:
                st.warning("⚠️ Instalează streamlit-autorefresh")
        
        st.markdown("---")
        
        # Acțiuni
        st.markdown("### 🛠️ Acțiuni")
        
        if st.button("🗑️ Golește Cache", use_container_width=True):
            cache_manager.clear_cache()
            st.cache_data.clear()
            st.success("✅ Cache golit!")
            time.sleep(1)
            st.rerun()
        
        if st.button("🔄 Reîncarcă Pagina", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # Despre
        st.markdown("### ℹ️ Despre")
        st.caption("""
        **Flight Search App** v1.0
        
        🔍 Caută zboruri ieftine din multiple surse
        
        **API-uri folosite:**
        - Amadeus (prețuri)
        - AirLabs (aeroporturi)
        - AeroDataBox (info)
        
        Made with ❤️ & Streamlit
        """)


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
            # Verificare selecție
            if not search_params['origin']:
                st.error("❌ Te rog selectează aeroportul de plecare!")
                st.stop()
            
            if not search_params['destination']:
                st.error("❌ Te rog selectează aeroportul de destinație!")
                st.stop()
            
            # Validare
            is_valid, errors = validate_search_params(
                origin=search_params['origin'],
                destination=search_params['destination'],
                departure_date=search_params['departure_date'],
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
                with st.spinner("🔍 Căutare în curs... Aceasta poate dura câteva secunde."):
                    service = st.session_state.flight_service
                    
                    try:
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
                        
                        if results:
                            st.success(f"✅ Am găsit {len(results)} zboruri!")
                        
                    except Exception as e:
                        st.error(f"❌ Eroare la căutare: {str(e)}")
                        st.session_state.search_results = []
        
        # Afișare rezultate
        if st.session_state.search_results:
            st.markdown("---")
            
            # Buton adăugare la monitor
            if st.session_state.last_search:
                with st.expander("📈 Adaugă la Monitorizare Prețuri"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        target_price = st.number_input(
                            "💰 Preț țintă (opțional)",
                            min_value=0.0,
                            value=0.0,
                            step=10.0,
                            help="Vei fi notificat când prețul scade sub această valoare"
                        )
                    
                    with col2:
                        st.markdown("")
                        st.markdown("")
                        if st.button("📈 Adaugă la Monitor", use_container_width=True):
                            params = st.session_state.last_search
                            service = st.session_state.flight_service
                            service.add_price_monitor(
                                origin=params['origin'],
                                destination=params['destination'],
                                departure_date=params['departure_date'],
                                target_price=target_price if target_price > 0 else None
                            )
                            st.success("✅ Rută adăugată la monitorizare!")
                            st.balloons()
            
            # Afișare rezultate
            currency = st.session_state.last_search.get('currency', 'EUR')
            display_flight_results(st.session_state.search_results, currency)
    
    with tab2:
        render_price_monitor()
    
    with tab3:
        render_airport_explorer()


# Rulare aplicație
if __name__ == "__main__":
    main()
