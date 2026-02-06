from flask import Flask, render_template
import sqlite3
import logging
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURATION WITH ABSOLUTE PATHS ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(PROJECT_DIR, "weather_data_10.db")
LOG_FILE = os.path.join(PROJECT_DIR, "app_debug.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s, %(message)s',
    datefmt='%Y-%m-%d, %H:%M:%S'
)

def get_temp_color(temp_val):
    """Returns a color hex code based on temperature with detailed gradient"""
    try:
        t = float(temp_val)
        if t < 0.0:
            return "#e1f5fe"  # Ice White-Blue (freezing)
        elif t < 5.0:
            return "#7c4dff"  # Purple (very cold)
        elif t < 10.0:
            return "#00bcd4"  # Cyan (cold)
        elif t < 18.0:
            return "#2196f3"  # Blue (cool)
        elif t <= 26.0:
            return "#ff9800"  # Orange (mild/pleasant)
        elif t <= 32.0:
            return "#f44336"  # Red (hot)
        elif t <= 40.0:
            return "#b71c1c"  # Dark Red (very hot)
        else:
            return "#880e4f"  # Deep Crimson (extreme heat)
    except:
        return "#1c1e21"      # Default Dark

def calculate_minute_value(temp_0, temp_1, temp_2, temp_3):
    """
    Calculate per-minute value: average of the 2 middle values from 4 sensors.
    Used only for calculating current display temperature.
    """
    temps = [t for t in [temp_0, temp_1, temp_2, temp_3] if t is not None]
    if len(temps) < 2:
        return None
    
    temps_sorted = sorted(temps)
    if len(temps_sorted) == 2:
        middle_two = temps_sorted
    elif len(temps_sorted) == 3:
        return temps_sorted[1]  # Just the middle one
    else:  # 4 values
        middle_two = temps_sorted[1:3]  # The 2 middle values
    
    return sum(middle_two) / len(middle_two)

def get_weather_data():
    conn = None
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    results = {
        "current": {
            "temps": [None, None, None, None],  # Temps for sensors 0-3
            "colors": ["#1c1e21", "#1c1e21", "#1c1e21", "#1c1e21"],
            "date": "N/A",
            "time": "N/A",
            "calculated_temp": "N/A",
            "calculated_color": "#1c1e21"
        },
        "graph_data_today": [],  # Today's 10-minute averages (from weather_graph_points)
        "graph_data_yesterday": [],  # Yesterday's 10-minute averages
        "graph_labels": [],  # Time labels for graph
        "control_panel": {
            "temp_4_current": "N/A",
            "cpu_current": "N/A",
            "temp_4_max": "N/A",
            "cpu_max": "N/A"
        },
        "global_stats": {
            "max_value": "N/A",
            "max_date": "N/A",
            "max_time": "N/A",
            "min_value": "N/A",
            "min_date": "N/A",
            "min_time": "N/A"
        }
    }
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # 1. Get current readings from weather_log (latest entry)
        cursor.execute("""
            SELECT temp_0, temp_1, temp_2, temp_3, temp_4, cpu_temp, log_date, log_time 
            FROM weather_log 
            ORDER BY id DESC LIMIT 1
        """)
        newest = cursor.fetchone()
        
        if newest:
            results["current"]["date"] = newest['log_date']
            results["current"]["time"] = newest['log_time']
            
            for i in range(4):
                temp_val = newest[f'temp_{i}']
                if temp_val is not None:
                    results["current"]["temps"][i] = "{:.2f}".format(temp_val)
                    results["current"]["colors"][i] = get_temp_color(temp_val)
                else:
                    results["current"]["temps"][i] = "N/A"
            
            # Calculate current display temperature (2 middle values average)
            current_calc = calculate_minute_value(
                newest['temp_0'], newest['temp_1'], newest['temp_2'], newest['temp_3']
            )
            if current_calc is not None:
                results["current"]["calculated_temp"] = "{:.2f}".format(current_calc)
                results["current"]["calculated_color"] = get_temp_color(current_calc)
            
            # Control panel: current temp_4 and CPU
            if newest['temp_4'] is not None:
                results["control_panel"]["temp_4_current"] = "{:.1f}".format(newest['temp_4'])
            if newest['cpu_temp'] is not None:
                results["control_panel"]["cpu_current"] = "{:.1f}".format(newest['cpu_temp'])
        
        # 2. Get control panel max values for today from weather_log
        cursor.execute("""
            SELECT MAX(temp_4) as max_temp_4, MAX(cpu_temp) as max_cpu 
            FROM weather_log 
            WHERE log_date = ?
        """, (today,))
        max_row = cursor.fetchone()
        if max_row:
            if max_row['max_temp_4'] is not None:
                results["control_panel"]["temp_4_max"] = "{:.1f}".format(max_row['max_temp_4'])
            if max_row['max_cpu'] is not None:
                results["control_panel"]["cpu_max"] = "{:.1f}".format(max_row['max_cpu'])
        
        # 3. Get graph data from weather_graph_points (pre-calculated 10-min averages)
        # Today's data
        cursor.execute("""
            SELECT log_time, calculated_temp 
            FROM weather_graph_points 
            WHERE log_date = ?
            ORDER BY log_time ASC
        """, (today,))
        today_points = cursor.fetchall()
        
        # Yesterday's data (for comparison)
        cursor.execute("""
            SELECT log_time, calculated_temp 
            FROM weather_graph_points 
            WHERE log_date = ?
            ORDER BY log_time ASC
        """, (yesterday,))
        yesterday_points = cursor.fetchall()
        
        # Create lookup dictionaries for fast access by time (HH:MM format)
        # Round times to nearest 10-minute boundary to handle any misaligned data
        today_lookup = {}
        for row in today_points:
            time_str = row['log_time'][:5] if len(row['log_time']) > 5 else row['log_time']
            # Round to nearest 10-minute boundary: 14:23 -> 14:20, 18:07 -> 18:00
            try:
                hour = int(time_str[:2])
                minute = int(time_str[3:5])
                rounded_minute = (minute // 10) * 10
                time_key = f"{hour:02d}:{rounded_minute:02d}"
            except:
                time_key = time_str
            today_lookup[time_key] = row['calculated_temp']
        
        yesterday_lookup = {}
        for row in yesterday_points:
            time_str = row['log_time'][:5] if len(row['log_time']) > 5 else row['log_time']
            try:
                hour = int(time_str[:2])
                minute = int(time_str[3:5])
                rounded_minute = (minute // 10) * 10
                time_key = f"{hour:02d}:{rounded_minute:02d}"
            except:
                time_key = time_str
            yesterday_lookup[time_key] = row['calculated_temp']
        
        # Build FIXED 24-hour graph with all 144 time slots (every 10 minutes)
        # This ensures the graph scale stays constant throughout the day
        for hour in range(24):
            for minute in range(0, 60, 10):
                time_label = f"{hour:02d}:{minute:02d}"
                results["graph_labels"].append(time_label)
                # Get data if available, otherwise None (will show as gap in graph)
                results["graph_data_today"].append(today_lookup.get(time_label))
                results["graph_data_yesterday"].append(yesterday_lookup.get(time_label))
        
        # 4. Get global stats from weather_stats table
        cursor.execute("""
            SELECT stat_name, stat_value, log_date, log_time 
            FROM weather_stats 
            WHERE stat_name IN ('global_max', 'global_min')
        """)
        stats_rows = cursor.fetchall()
        
        for stat in stats_rows:
            if stat['stat_name'] == 'global_max' and stat['stat_value'] is not None:
                results["global_stats"]["max_value"] = "{:.1f}".format(stat['stat_value'])
                results["global_stats"]["max_date"] = stat['log_date'] or "N/A"
                results["global_stats"]["max_time"] = stat['log_time'] or "N/A"
            elif stat['stat_name'] == 'global_min' and stat['stat_value'] is not None:
                results["global_stats"]["min_value"] = "{:.1f}".format(stat['stat_value'])
                results["global_stats"]["min_date"] = stat['log_date'] or "N/A"
                results["global_stats"]["min_time"] = stat['log_time'] or "N/A"
            
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
        calculated_temp=data["current"]["calculated_temp"],
        calculated_color=data["current"]["calculated_color"],
        graph_data_today=data["graph_data_today"],
        graph_data_yesterday=data["graph_data_yesterday"],
        graph_labels=data["graph_labels"],
        control_panel=data["control_panel"],
        global_stats=data["global_stats"]
    )

if __name__ == '__main__':
    logging.info("System Startup: weather_flask_app.py - Simplified with pre-calculated data")
    app.run(host='0.0.0.0', port=5000, debug=True)
