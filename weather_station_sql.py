import sqlite3
import weather_station_config as config

def init_db():
    """Initializes the database and creates the table structure."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    # Table includes: ID, Date, Time, Ambient Temp, and CPU Temp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,
            log_time TEXT,
            ambient_temp REAL,
            cpu_temp REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_reading(date, time, ambient, cpu):
    """Inserts a single log entry into the database."""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO weather_log (log_date, log_time, ambient_temp, cpu_temp)
            VALUES (?, ?, ?, ?)
        ''', (date, time, ambient, cpu))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQL Error: {e}")
