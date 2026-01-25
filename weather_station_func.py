import os
import time
import logging
from temp_sen_char.sensor_map import SENSOR_MAP

BASE_DIR = '/sys/bus/w1/devices/'

# Configure logging for sensor errors
logging.basicConfig(
    filename='sensor_errors.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    Reads the DS18B20 sensor by index and returns a single temperature measurement.
    
    Args:
        sensor_index: Index of the sensor (0-4) as defined in SENSOR_MAP
        
    Returns:
        Temperature in Celsius, or None on failure (error is logged)
    """
    try:
        # Get the serial number for this sensor index
        if sensor_index not in SENSOR_MAP:
            logging.warning(f"Sensor {sensor_index}: Invalid sensor index (not in SENSOR_MAP)")
            return None
        
        sensor_serial = SENSOR_MAP[sensor_index]
        device_file = os.path.join(BASE_DIR, sensor_serial, 'w1_slave')
        
        # Check if the sensor device exists
        if not os.path.exists(device_file):
            logging.warning(f"Sensor {sensor_index} ({sensor_serial}): Device file not found")
            return None

        # Single read (no loop needed)
        with open(device_file, 'r') as f:
            lines = f.readlines()
        
        # Check CRC result
        if len(lines) < 2:
            logging.warning(f"Sensor {sensor_index} ({sensor_serial}): Incomplete response")
            return None
            
        if 'YES' not in lines[0]:
            logging.warning(f"Sensor {sensor_index} ({sensor_serial}): CRC check failed")
            return None
        
        # Extract temperature
        try:
            temp_string = lines[1].split('t=')[1]
            temp_celsius = float(temp_string) / 1000.0
            
            # Sanity check for valid temperature range
            if temp_celsius < -55 or temp_celsius > 125:
                logging.warning(f"Sensor {sensor_index} ({sensor_serial}): Temperature out of range ({temp_celsius}°C)")
                return None
            
            return temp_celsius
        except (IndexError, ValueError) as e:
            logging.warning(f"Sensor {sensor_index} ({sensor_serial}): Failed to parse temperature - {e}")
            return None
            
    except Exception as e:
        logging.error(f"Sensor {sensor_index}: Unexpected error - {e}")
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
