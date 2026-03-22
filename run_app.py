import subprocess
import sys
import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import numpy as np
from datetime import datetime
import urllib3

def run():
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "smartCargo.py"
    ])

if __name__ == "__main__":
    run()


# old logic
def get_air_data():
    """Fetches live data using OpenSky Credentials with updated column mapping"""
    try:
        url = "https://opensky-network.org/api/states/all"
        response = requests.get(
            url, 
            #auth=(OS_USERNAME, OS_PASSWORD), 
            timeout=15, 
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            states = data.get('states')
            
            if states:
                all_cols = [
                    'icao24', 'callsign', 'origin_country', 'time_pos', 'last_contact', 
                    'lon', 'lat', 'alt', 'on_ground', 'velocity', 'true_track', 
                    'vertical_rate', 'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
                ]
                df = pd.DataFrame(states, columns=all_cols)
                df = df.dropna(subset=['lon', 'lat']).head(150)
                return df, "🟢 Live Satellite Feed"
        
        elif response.status_code == 401:
            return pd.DataFrame(), "🔴 Error: Invalid Credentials (401)"
            
    except Exception:
        pass 