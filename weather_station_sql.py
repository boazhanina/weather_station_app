import sqlite3
import weather_station_config as config

def init_db():
    """Initializes the database and creates the table structure."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    # Table includes: ID, Date, Time, 5 Temperature columns (one per sensor), and CPU Temp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,
            log_time TEXT,
            temp_0 REAL,
            temp_1 REAL,
            temp_2 REAL,
            temp_3 REAL,
            temp_4 REAL,
            cpu_temp REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_reading(date, time, temperatures, cpu):
    """
    Inserts a single log entry with all 5 sensor temperatures.
    
    Args:
        date: Date string (YYYY-MM-DD)
        time: Time string (HH:MM:SS)
        temperatures: Dictionary with sensor_index (0-4) as key and temperature as value
        cpu: CPU temperature
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO weather_log (log_date, log_time, temp_0, temp_1, temp_2, temp_3, temp_4, cpu_temp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date, 
            time, 
            temperatures.get(0), 
            temperatures.get(1), 
            temperatures.get(2), 
            temperatures.get(3), 
            temperatures.get(4), 
            cpu
        ))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQL Error: {e}")
