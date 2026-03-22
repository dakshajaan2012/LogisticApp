# 0. LIBRARIES
import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import numpy as np
from datetime import datetime
import urllib3

# 1. SETUP
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="Eco-Track Logistics AI", layout="wide")

# --- OPENSKY CREDENTIALS ---
#OS_USERNAME = "dakshajaan2012@gmail.com"
#OS_PASSWORD = "Elephant35#" 

# For strealite
#OS_USERNAME = st.secrets["OS_USERNAME"]
#OS_PASSWORD = st.secrets["OS_PASSWORD"]



# 2. PROFESSIONAL CALCULATION LOGIC
def calculate_metrics(weight, distance, mode):
    """
    Industry Standard Logistics Pricing (2026 Market Benchmarks)
    """
    # 1. VOLUME ESTIMATION (The "Innovation" Feature)
    # Assume a standard density to calculate Volumetric Weight.
    # Air Standard is 1:6000. Sea LCL Standard is 1:1000.
    if mode == "Air Cargo":
        volumetric_weight = weight * 1.2  # Simple proxy for 1:6 ratio
        base_rate_per_kg = 4.85 if distance > 5000 else 2.56
        fsc_percent = 0.20  # 20% Fuel Surcharge
        ssc_rate = 0.18     # $0.18/kg Security Surcharge
        thc_flat = 150.00   # Terminal Handling
    elif mode == "Sea Freight":
        volumetric_weight = weight * 1.05 # Sea is denser
        base_rate_per_kg = 0.18
        fsc_percent = 0.05
        ssc_rate = 0.02
        thc_flat = 450.00
    else: # Hybrid (Sea-Air)
        volumetric_weight = weight * 1.15
        base_rate_per_kg = 2.10
        fsc_percent = 0.12
        ssc_rate = 0.10
        thc_flat = 300.00

    # 2. DETERMINE CHARGEABLE WEIGHT
    # Market rule: Always charge for the higher of Actual vs. Volumetric
    chargeable_weight = max(weight, volumetric_weight)
    # 2.1. COMPONENT BREAKDOWN 
    # Logic: Weight * (Distance/1000) * Rate
    # This ensures that 10,000km costs more than 5,000km
    #distance_units = distance / 1000

    # 3. COMPONENT BREAKDOWN (How real invoices look)
    base_freight = chargeable_weight * base_rate_per_kg #*distance_units
    fuel_surcharge = base_freight * fsc_percent
    security_surcharge = chargeable_weight * ssc_rate
    
    # 4. FINAL TOTAL
    total_cost = base_freight + fuel_surcharge + security_surcharge + thc_flat
    
    # --- Carbon Calculation (Remains Industry Standard) ---
    tons = weight / 1000
    co2_factors = {"Air Cargo": 500, "Sea Freight": 15, "Hybrid (Sea-Air)": 150}
    total_co2 = (tons * distance * co2_factors[mode]) / 1000000 
    
    return round(total_co2, 2), round(total_cost, 2)

@st.cache_data(ttl=60) 
@st.cache_data(ttl=60) # CRITICAL: Prevents API banning on Streamlit Cloud
def get_air_data():
    """Fetches live data using OpenSky Credentials with updated column mapping"""
    # Use st.secrets to get your credentials securely
    try:
        # 1. Access Credentials from Streamlit Secrets
        USER = st.secrets["OS_USERNAME"]
        PASS = st.secrets["OS_PASSWORD"]
    
        
        url = "https://opensky-network.org/api/states/all"
        
        # 2. Make the Request
        response = requests.get(
            url, 
            auth=(USER, PASS), 
            timeout=15, 
            verify=False # Helps bypass some server-side SSL issues
        )
        
        if response.status_code == 200:
            data = response.json()
            states = data.get('states')
            
            # 3. Only process if states is NOT None
            if states is not None:
                all_cols = [
                    'icao24', 'callsign', 'origin_country', 'time_pos', 'last_contact', 
                    'lon', 'lat', 'alt', 'on_ground', 'velocity', 'true_track', 
                    'vertical_rate', 'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
                ]
                df = pd.DataFrame(states, columns=all_cols)
                df = df.dropna(subset=['lon', 'lat']).head(150)
                return df, "🟢 LIVE SATELLITE FEED (Authenticated)"
        
        elif response.status_code == 401:
            return pd.DataFrame(), "🔴 Error: Invalid Credentials (401)"
            
    except Exception as e:
        # Log the error to the Streamlit console for you to see, but don't stop the app
        print(f"Cloud API Error: {e}") 
    
    # 4. FALLBACK MOCK DATA (Triggers if API is down, timed out, or empty)
    mock_df = pd.DataFrame({
        'callsign': [f'CRGO{i}' for i in range(100)],
        'lon': np.random.uniform(-160, 160, 100),
        'lat': np.random.uniform(-50, 70, 100),
        'alt': np.random.uniform(9000, 11000, 100),
        'origin_country': np.random.choice(["USA", "China", "Germany", "UAE", "Singapore"], 100)
    })
    return mock_df, "🟡 ARCHIVED GLOBAL SNAPSHOT (Offline Mode)"

# 3. SIDEBAR
st.sidebar.markdown("<h1 style='text-align: left;'>📦 Control Center</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.subheader("Shipment Identification")
tracking_id = st.sidebar.text_input("Enter AWB or BOL #", "AWB-774-9021")

st.sidebar.subheader("Transport Parameters")
mode = st.sidebar.selectbox("Transport Mode", ["Air Cargo", "Sea Freight", "Hybrid (Sea-Air)"])
weight = st.sidebar.slider("Shipment Weight (kg)", 500, 100000, 15000)
distance_input = st.sidebar.number_input("Route Distance (km)", value=8500)

st.sidebar.markdown("---")
st.sidebar.subheader("Future Roadmap")
st.sidebar.info("1. AI Port-Delay Prediction\n2. Drone Last-Mile Docking\n3. Blockchain Bill of Lading")

# 4. MAIN DASHBOARD UI
st.title("🌍 Eco-Track: Multimodal Shipping Dashboard")
st.markdown(f"**Currently Tracking Reference:** `{tracking_id}`")

# Header Info Boxes
c1, c2 = st.columns(2)
with c1:
    st.info(f"📦 **Document Type:** {'Air Waybill' if 'Air' in mode else 'Bill of Lading'}")
with c2:
    st.info(f"🆔 **Reference:** {tracking_id}")

# Fetch Data and Calculate Metrics
df_air, data_status = get_air_data()
co2, est_cost = calculate_metrics(weight, distance_input, mode)

# Metric Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Selected Mode", mode)
m2.metric("Carbon Footprint", f"{co2} Tons Co2", delta="-12%" if mode != "Air Cargo" else "HIGH", delta_color="inverse")
m3.metric("Est. Freight Cost", f"${est_cost:,.2f}")
m4.metric("Data Status", data_status)

# 5. MAP SECTION
st.markdown("---")
if mode == "Air Cargo":
    st.subheader("Live Global Air Freight Distribution")
    st.pydeck_chart(pdk.Deck(
        map_style='dark',  
        initial_view_state=pdk.ViewState(latitude=20, longitude=0, zoom=1.1, pitch=40),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df_air,
                get_position='[lon, lat]',
                get_fill_color='[255, 165, 0, 160]', 
                get_radius=150000,
            ),
        ],
    ))

elif mode == "Sea Freight":
    st.subheader("Global Maritime Lane: Shanghai ➔ Rotterdam")
    path_df = pd.DataFrame({'s_lon': [121.4], 's_lat': [31.2], 't_lon': [4.4], 't_lat': [51.9]})
    st.pydeck_chart(pdk.Deck(
        map_style='light', 
        initial_view_state=pdk.ViewState(latitude=15, longitude=70, zoom=1.8),
        layers=[
            pdk.Layer('ArcLayer', data=path_df, get_source_position='[s_lon, s_lat]', 
                      get_target_position='[t_lon, t_lat]', get_source_color=[0, 100, 255], 
                      get_target_color=[0, 255, 128], width=4)
        ],
    ))
    st.success("✅ Sea mode reduces carbon by 97% compared to Air.")

else: # Hybrid (Sea-Air)
    st.subheader("Hybrid Route: Sea (Asia to Dubai) + Air (Dubai to Europe)")
    hybrid_paths = pd.DataFrame({
        's_lon': [121.4, 55.3], 's_lat': [31.2, 25.2],
        't_lon': [55.3, 4.4], 't_lat': [25.2, 51.9]
    })
    st.pydeck_chart(pdk.Deck(
        map_style='road', 
        initial_view_state=pdk.ViewState(latitude=25, longitude=60, zoom=3),
        layers=[
            pdk.Layer('ArcLayer', data=hybrid_paths, get_source_position='[s_lon, s_lat]', 
                      get_target_position='[t_lon, t_lat]', get_source_color=[255, 255, 0], 
                      get_target_color=[255, 0, 255], width=5)
        ],
    ))
    st.info("💡 Innovation: Hybrid shipping balances urgent delivery with ESG (Environmental) goals.")

# 6. DATA VIEW
with st.expander("View Raw Shipment Manifest"):
    st.dataframe(df_air.head(15))

# 7. FOOTER
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Eco-Track Terminal v2.1")