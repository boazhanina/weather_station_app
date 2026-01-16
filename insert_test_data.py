#!/usr/bin/env python3
"""
Inserts dummy test data into the database for testing the web dashboard.
Run this to verify the Flask app and Cloudflare tunnel work correctly.
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "weather_data_10.db"

def create_table():
    """Create the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    print("Table created/verified.")

def insert_test_data(hours=24):
    """Insert test data for the specified number of hours."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Start from 'hours' ago
    start_time = datetime.now() - timedelta(hours=hours)
    
    # Insert one record every 5 minutes
    records_inserted = 0
    for i in range(hours * 12):  # 12 records per hour (every 5 min)
        current_time = start_time + timedelta(minutes=i * 5)
        
        # Generate realistic temperature data (base + variation)
        base_temp = 22 + 5 * (0.5 - abs((current_time.hour - 14) / 14))  # Peak at 2pm
        
        temp_0 = base_temp + random.uniform(-1, 1)
        temp_1 = base_temp + random.uniform(-1.5, 1.5)
        temp_2 = base_temp + random.uniform(-0.5, 0.5)
        temp_3 = base_temp + random.uniform(-1, 1)
        temp_4 = base_temp + random.uniform(2, 5)  # Sensor 4 is inside box (warmer)
        cpu_temp = 45 + random.uniform(-5, 10)
        
        cursor.execute('''
            INSERT INTO weather_log (log_date, log_time, temp_0, temp_1, temp_2, temp_3, temp_4, cpu_temp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_time.strftime("%Y-%m-%d"),
            current_time.strftime("%H:%M:%S"),
            round(temp_0, 2),
            round(temp_1, 2),
            round(temp_2, 2),
            round(temp_3, 2),
            round(temp_4, 2),
            round(cpu_temp, 1)
        ))
        records_inserted += 1
    
    conn.commit()
    conn.close()
    print(f"Inserted {records_inserted} test records (last {hours} hours).")

if __name__ == "__main__":
    print("=" * 50)
    print("Inserting Test Data for Weather Dashboard")
    print("=" * 50)
    create_table()
    insert_test_data(24)  # 24 hours of data
    print("Done! You can now test the Flask app.")
    print("=" * 50)
