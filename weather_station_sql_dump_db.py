import sqlite3
import os
import sys

def format_temp(temp):
    """Formats temperature value, handling None values."""
    if temp is None:
        return "   N/A "
    return f"{temp:>6.2f}°"

def fetch_all_data(db_name):
    """
    Fetches and displays all data from the specified SQLite database.
    
    Args:
        db_name: Name of the database file (e.g., 'weather_data_10.db')
    """
    # Check if the database file exists first
    if not os.path.exists(db_name):
        print(f"Error: Database file '{db_name}' not found.")
        return

    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Query to get everything with all 5 temperature columns
        cursor.execute("""
            SELECT id, log_date, log_time, temp_0, temp_1, temp_2, temp_3, temp_4, cpu_temp 
            FROM weather_log
            ORDER BY id
        """)
        rows = cursor.fetchall()

        if not rows:
            print(f"The database '{db_name}' is empty.")
            return

        # Print Table Header
        print(f"\nDatabase: {db_name}")
        print("=" * 115)
        print(f"{'ID':<6} | {'Date':<12} | {'Time':<10} | {'Temp 0':>7} | {'Temp 1':>7} | {'Temp 2':>7} | {'Temp 3':>7} | {'Temp 4':>7} | {'CPU':>7}")
        print("-" * 115)

        # Print each row
        for row in rows:
            db_id, date, time, t0, t1, t2, t3, t4, cpu = row
            print(f"{db_id:<6} | {date:<12} | {time:<10} | "
                  f"{format_temp(t0)} | {format_temp(t1)} | {format_temp(t2)} | "
                  f"{format_temp(t3)} | {format_temp(t4)} | {format_temp(cpu)}")

        print("-" * 115)
        print(f"Total Records: {len(rows)}")
        print("=" * 115 + "\n")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def print_usage():
    """Prints usage information."""
    print("Usage: python3 weather_station_sql_dump_db.py <database_name>")
    print("Example: python3 weather_station_sql_dump_db.py weather_data_10.db")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Database name is required.")
        print_usage()
        sys.exit(1)
    
    db_name = sys.argv[1]
    fetch_all_data(db_name)
