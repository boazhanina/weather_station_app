import os
import time
import statistics  # Library for median calculation
import weather_station_config as config
from temp_sen_char.sensor_map import SENSOR_MAP

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

def get_ambient_temp_single_sensor(sensor_index):
    """
    Reads the DS18B20 sensor by index and returns MEDIAN temperature to filter noise.
    
    Args:
        sensor_index: Index of the sensor (0-4) as defined in SENSOR_MAP
        
    Returns:
        Median temperature in Celsius, or None on failure
    """
    readings = []
    try:
        # Get the serial number for this sensor index
        if sensor_index not in SENSOR_MAP:
            return None
        
        sensor_serial = SENSOR_MAP[sensor_index]
        device_file = os.path.join(BASE_DIR, sensor_serial, 'w1_slave')
        
        # Check if the sensor device exists
        if not os.path.exists(device_file):
            return None

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

def get_ambient_temp():
    """
    Reads all 5 DS18B20 temperature sensors and returns their measurements.
    
    Returns:
        Dictionary with sensor_index as key and temperature (or None) as value.
        Example: {0: 23.5, 1: 24.1, 2: None, 3: 22.8, 4: 23.0}
    """
    measurements = {}
    for sensor_index in SENSOR_MAP.keys():
        temp = get_ambient_temp_single_sensor(sensor_index)
        measurements[sensor_index] = temp
    return measurements

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
