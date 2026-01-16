import os
import time
import statistics  # Library for median calculation
import weather_station_config as config

BASE_DIR = '/sys/bus/w1/devices/'

def set_power_state(on):
    """Turns WiFi and HDMI On (True) or Off (False) to save power."""
    if on:
        # Turn ON HDMI and WiFi
        os.system("vcgencmd display_power 1 > /dev/null")
        os.system("sudo rfkill unblock wifi")
        # Critical: WiFi needs time to reconnect to the router
        time.sleep(10)
    else:
        # Turn OFF HDMI and WiFi
        os.system("vcgencmd display_power 0 > /dev/null")
        os.system("sudo rfkill block wifi")

def get_ambient_temp():
    """Reads the DS18B20 sensor and returns MEDIAN temperature to filter noise."""
    readings = []
    try:
        device_folders = [f for f in os.listdir(BASE_DIR) if f.startswith('28-')]
        if not device_folders: return None
        device_file = os.path.join(BASE_DIR, device_folders[0], 'w1_slave')

        for _ in range(config.TEMP_AVG_ITERATIONS):
            with open(device_file, 'r') as f:
                lines = f.readlines()
            if 'YES' in lines[0]:
                temp_string = lines[1].split('t=')[1]
                readings.append(float(temp_string) / 1000.0)
            time.sleep(0.1)
        
        # Calculate median instead of average
        return statistics.median(readings) if readings else None
    except Exception:
        return None

def get_cpu_temp():
    """Reads the Raspberry Pi internal CPU temperature."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = f.read()
        return float(temp) / 1000.0
    except:
        return 0.0

def get_color_code(temp):
    """Returns terminal color codes based on temperature value."""
    if temp is None: return "\033[0m"
    if temp <= 15: return "\033[1;34m"
    elif temp <= 25: return "\033[1;32m"
    elif temp <= 32: return "\033[1;33m"
    else: return "\033[1;31m"

def get_reset_code():
    """Returns the terminal color reset code."""
    return "\033[0m"
