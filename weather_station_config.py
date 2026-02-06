# --- Weather Station Settings ---
SLEEP_TIME = 60          # 1 minute (60 seconds) between readings
TEMP_AVG_ITERATIONS = 1  # Single measurement per sensor (no averaging)

# --- Power Management ---
LOW_POWER_MODE = False     # Set to False to keep WiFi/HDMI always ON
SYNC_WINDOW = 30          # Seconds to stay awake for Laptop/Samba sync

# --- Database Settings ---
import os
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(PROJECT_DIR, "weather_data_10.db")

# --- Color Scale Settings ---
MIN_TEMP = 0   
MAX_TEMP = 40
