import sqlite3
import os
import weather_station_config as config

def fetch_all_data():
    # Check if the database file exists first
    if not os.path.exists(config.DB_NAME):
        print(f"Error: Database file '{config.DB_NAME}' not found.")
        return

    try:
        # Connect to the database
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()

        # Query to get everything
        cursor.execute("SELECT id, log_date, log_time, ambient_temp, cpu_temp FROM weather_log")
        rows = cursor.fetchall()

        if not rows:
            print("The database is empty.")
            return

        # Print Table Header
        print("\n" + "="*70)
        print(f"{'ID':<5} | {'Date':<12} | {'Time':<10} | {'Ambient':<10} | {'CPU Temp':<10}")
        print("-" * 70)

        # Print each row
        for row in rows:
            db_id, date, time, amb, cpu = row
            print(f"{db_id:<5} | {date:<12} | {time:<10} | {amb:>7.2f}°C | {cpu:>7.2f}°C")

        print("-" * 70)
        print(f"Total Records: {len(rows)}")
        print("="*70 + "\n")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fetch_all_data()
