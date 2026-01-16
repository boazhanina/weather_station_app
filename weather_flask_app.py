from flask import Flask, render_template
import sqlite3
import logging
import os
import statistics

app = Flask(__name__)

# --- CONFIGURATION ---
DB_NAME = "weather_data_10.db"
LOG_FILE = "app_debug.log"

# Sensor colors for the graph (distinct colors for each sensor)
SENSOR_COLORS = {
    0: "#e74c3c",  # Red
    1: "#3498db",  # Blue
    2: "#2ecc71",  # Green
    3: "#9b59b6",  # Purple
}

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s, %(message)s',
    datefmt='%Y-%m-%d, %H:%M:%S'
)

def get_temp_color(temp_val):
    """Returns a color hex code based on temperature"""
    try:
        t = float(temp_val)
        if t < 18.0:
            return "#007bff"  # Cold Blue
        elif t <= 26.0:
            return "#ff9800"  # Mild Orange
        else:
            return "#f44336"  # Hot Red
    except:
        return "#1c1e21"      # Default Dark

def get_weather_data():
    conn = None
    results = {
        "current": {
            "temps": [None, None, None, None],  # Temps for sensors 0-3
            "colors": ["#1c1e21", "#1c1e21", "#1c1e21", "#1c1e21"],
            "date": "N/A",
            "time": "N/A"
        },
        "history": {
            0: [],
            1: [],
            2: [],
            3: []
        },
        "median_history": [],
        "labels": [],
        "sensor_colors": SENSOR_COLORS,
        "control_panel": {
            "temp_4_current": "N/A",
            "cpu_current": "N/A",
            "temp_4_max": "N/A",
            "cpu_max": "N/A"
        }
    }
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Fetch last 288 measurements (24 hours at 5-min intervals)
        cursor.execute("""
            SELECT temp_0, temp_1, temp_2, temp_3, temp_4, cpu_temp, log_date, log_time 
            FROM weather_log 
            ORDER BY id DESC 
            LIMIT 288
        """)
        rows = cursor.fetchall()
        
        if rows:
            # Get current (newest) readings
            newest = rows[0]
            results["current"]["date"] = newest['log_date']
            results["current"]["time"] = newest['log_time']
            
            for i in range(4):
                temp_val = newest[f'temp_{i}']
                if temp_val is not None:
                    results["current"]["temps"][i] = "{:.2f}".format(temp_val)
                    results["current"]["colors"][i] = get_temp_color(temp_val)
                else:
                    results["current"]["temps"][i] = "N/A"
            
            # Control panel: current temp_4 and CPU
            if newest['temp_4'] is not None:
                results["control_panel"]["temp_4_current"] = "{:.1f}".format(newest['temp_4'])
            if newest['cpu_temp'] is not None:
                results["control_panel"]["cpu_current"] = "{:.1f}".format(newest['cpu_temp'])
            
            # Control panel: max temp_4 and CPU for last 24 hours
            temp_4_values = [r['temp_4'] for r in rows if r['temp_4'] is not None]
            cpu_values = [r['cpu_temp'] for r in rows if r['cpu_temp'] is not None]
            
            if temp_4_values:
                results["control_panel"]["temp_4_max"] = "{:.1f}".format(max(temp_4_values))
            if cpu_values:
                results["control_panel"]["cpu_max"] = "{:.1f}".format(max(cpu_values))
            
            # Build history for each sensor (reversed to chronological order)
            for r in reversed(rows):
                results["labels"].append(r['log_time'])
                row_temps = []
                for i in range(4):
                    temp_val = r[f'temp_{i}']
                    results["history"][i].append(
                        round(temp_val, 2) if temp_val is not None else None
                    )
                    if temp_val is not None:
                        row_temps.append(temp_val)
                
                # Calculate median of the 4 sensors for this measurement point
                if row_temps:
                    median_val = statistics.median(row_temps)
                    results["median_history"].append(round(median_val, 2))
                else:
                    results["median_history"].append(None)
            
    except Exception as e:
        logging.error(f"DATABASE ERROR: {str(e)}")
    finally:
        if conn:
            conn.close()
            
    return results

@app.route('/')
def index():
    logging.info("demand for new data from the html frontend side")
    data = get_weather_data()
    
    return render_template(
        'index.html',
        temps=data["current"]["temps"],
        colors=data["current"]["colors"],
        date=data["current"]["date"],
        time=data["current"]["time"],
        labels=data["labels"],
        history=data["history"],
        median_history=data["median_history"],
        sensor_colors=data["sensor_colors"],
        control_panel=data["control_panel"]
    )

if __name__ == '__main__':
    logging.info("System Startup: weather_flask_app.py with 4 Sensors")
    app.run(host='0.0.0.0', port=5000, debug=True)
