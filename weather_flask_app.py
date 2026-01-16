from flask import Flask, render_template
import sqlite3
import logging
import os

app = Flask(__name__)

# --- CONFIGURATION ---
DB_NAME = "weather_data_10.db"
LOG_FILE = "app_debug.log"

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
        "current": {"temp": "0.00", "date": "N/A", "time": "N/A", "color": "#1c1e21"},
        "history": []
    }
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Fetch last 288 measurements
        cursor.execute("SELECT ambient_temp, log_date, log_time FROM weather_log ORDER BY id DESC LIMIT 288")
        rows = cursor.fetchall()
        
        if rows:
            newest = rows[0]
            temp_val = newest['ambient_temp']
            results["current"]["temp"] = "{:.2f}".format(temp_val)
            results["current"]["date"] = newest['log_date']
            results["current"]["time"] = newest['log_time']
            # Determine color for the big display
            results["current"]["color"] = get_temp_color(temp_val)
            
            for r in reversed(rows):
                results["history"].append({
                    "temp": round(r['ambient_temp'], 2),
                    "label": f"{r['log_time']}"
                })
            
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
        temp=data["current"]["temp"],
        date=data["current"]["date"],
        time=data["current"]["time"],
        color=data["current"]["color"],  # Pass the color to the template
        history=data["history"]
    )

if __name__ == '__main__':
    logging.info("System Startup: weather_flask_app.py with Dynamic Colors")
    app.run(host='0.0.0.0', port=5000, debug=True)
