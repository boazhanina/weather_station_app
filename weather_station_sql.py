import sqlite3
import weather_station_config as config

def init_db():
    """Initializes the database and creates all table structures."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    # Table 1: Raw sensor data (every minute)
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
    
    # Table 2: Graph points (every 10 minutes, pre-calculated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_graph_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,
            log_time TEXT,
            calculated_temp REAL
        )
    ''')
    
    # Table 3: Global statistics (max/min)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_stats (
            stat_name TEXT PRIMARY KEY,
            stat_value REAL,
            log_date TEXT,
            log_time TEXT
        )
    ''')
    
    # Initialize stats if they don't exist
    cursor.execute('''
        INSERT OR IGNORE INTO weather_stats (stat_name, stat_value, log_date, log_time)
        VALUES ('global_max', NULL, NULL, NULL)
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO weather_stats (stat_name, stat_value, log_date, log_time)
        VALUES ('global_min', NULL, NULL, NULL)
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

def save_graph_point(date, time, calculated_temp):
    """
    Saves a 10-minute averaged graph point.
    
    Args:
        date: Date string (YYYY-MM-DD)
        time: Time string (HH:MM)
        calculated_temp: The calculated average temperature
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO weather_graph_points (log_date, log_time, calculated_temp)
            VALUES (?, ?, ?)
        ''', (date, time, calculated_temp))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQL Error saving graph point: {e}")

def update_global_stats(calculated_temp, date, time):
    """
    Updates global max/min if the new value beats the current record.
    
    Args:
        calculated_temp: The calculated average temperature
        date: Date string (YYYY-MM-DD)
        time: Time string (HH:MM)
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Check and update global max
        cursor.execute('SELECT stat_value FROM weather_stats WHERE stat_name = "global_max"')
        row = cursor.fetchone()
        current_max = row[0] if row and row[0] is not None else None
        
        if current_max is None or calculated_temp > current_max:
            cursor.execute('''
                UPDATE weather_stats 
                SET stat_value = ?, log_date = ?, log_time = ?
                WHERE stat_name = "global_max"
            ''', (calculated_temp, date, time))
        
        # Check and update global min
        cursor.execute('SELECT stat_value FROM weather_stats WHERE stat_name = "global_min"')
        row = cursor.fetchone()
        current_min = row[0] if row and row[0] is not None else None
        
        if current_min is None or calculated_temp < current_min:
            cursor.execute('''
                UPDATE weather_stats 
                SET stat_value = ?, log_date = ?, log_time = ?
                WHERE stat_name = "global_min"
            ''', (calculated_temp, date, time))
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQL Error updating stats: {e}")

def get_global_stats():
    """
    Retrieves global max and min statistics.
    
    Returns:
        Dictionary with 'max' and 'min' keys, each containing value, date, time
    """
    result = {
        'max': {'value': None, 'date': None, 'time': None},
        'min': {'value': None, 'date': None, 'time': None}
    }
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT stat_value, log_date, log_time FROM weather_stats WHERE stat_name = "global_max"')
        row = cursor.fetchone()
        if row and row[0] is not None:
            result['max'] = {'value': row[0], 'date': row[1], 'time': row[2]}
        
        cursor.execute('SELECT stat_value, log_date, log_time FROM weather_stats WHERE stat_name = "global_min"')
        row = cursor.fetchone()
        if row and row[0] is not None:
            result['min'] = {'value': row[0], 'date': row[1], 'time': row[2]}
        
        conn.close()
    except sqlite3.Error as e:
        print(f"SQL Error reading stats: {e}")
    
    return result
