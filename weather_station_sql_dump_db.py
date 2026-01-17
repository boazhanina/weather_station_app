import sqlite3
import os
import sys

def format_temp(temp):
    """Formats temperature value, handling None values."""
    if temp is None:
        return "   N/A "
    return f"{temp:>6.2f}°"

def dump_weather_log(cursor):
    """Dumps the weather_log table (raw sensor data)."""
    cursor.execute("""
        SELECT id, log_date, log_time, temp_0, temp_1, temp_2, temp_3, temp_4, cpu_temp 
        FROM weather_log
        ORDER BY id
    """)
    rows = cursor.fetchall()

    print("\n" + "=" * 115)
    print("TABLE: weather_log (Raw Sensor Data - Every Minute)")
    print("=" * 115)
    
    if not rows:
        print("  (empty)")
    else:
        print(f"{'ID':<6} | {'Date':<12} | {'Time':<10} | {'Temp 0':>7} | {'Temp 1':>7} | {'Temp 2':>7} | {'Temp 3':>7} | {'Temp 4':>7} | {'CPU':>7}")
        print("-" * 115)

        for row in rows:
            db_id, date, time, t0, t1, t2, t3, t4, cpu = row
            print(f"{db_id:<6} | {date:<12} | {time:<10} | "
                  f"{format_temp(t0)} | {format_temp(t1)} | {format_temp(t2)} | "
                  f"{format_temp(t3)} | {format_temp(t4)} | {format_temp(cpu)}")

        print("-" * 115)
        print(f"Total Records: {len(rows)}")
    
    return len(rows)

def dump_graph_points(cursor):
    """Dumps the weather_graph_points table (10-minute averages)."""
    cursor.execute("""
        SELECT id, log_date, log_time, calculated_temp 
        FROM weather_graph_points
        ORDER BY id
    """)
    rows = cursor.fetchall()

    print("\n" + "=" * 70)
    print("TABLE: weather_graph_points (10-Minute Averages)")
    print("=" * 70)
    
    if not rows:
        print("  (empty)")
    else:
        print(f"{'ID':<6} | {'Date':<12} | {'Time':<8} | {'Calculated Temp':>15}")
        print("-" * 70)

        for row in rows:
            db_id, date, time, calc_temp = row
            temp_str = f"{calc_temp:>14.2f}°" if calc_temp is not None else "           N/A"
            print(f"{db_id:<6} | {date:<12} | {time:<8} | {temp_str}")

        print("-" * 70)
        print(f"Total Graph Points: {len(rows)}")
    
    return len(rows)

def dump_stats(cursor):
    """Dumps the weather_stats table (global max/min)."""
    cursor.execute("""
        SELECT stat_name, stat_value, log_date, log_time 
        FROM weather_stats
        ORDER BY stat_name
    """)
    rows = cursor.fetchall()

    print("\n" + "=" * 70)
    print("TABLE: weather_stats (Global Statistics)")
    print("=" * 70)
    
    if not rows:
        print("  (empty)")
    else:
        print(f"{'Stat Name':<15} | {'Value':>10} | {'Date':<12} | {'Time':<8}")
        print("-" * 70)

        for row in rows:
            stat_name, stat_value, log_date, log_time = row
            value_str = f"{stat_value:>9.2f}°" if stat_value is not None else "      N/A"
            date_str = log_date if log_date else "N/A"
            time_str = log_time if log_time else "N/A"
            print(f"{stat_name:<15} | {value_str} | {date_str:<12} | {time_str:<8}")

        print("-" * 70)
    
    return len(rows)

def fetch_all_data(db_name):
    """
    Fetches and displays all data from all tables in the database.
    
    Args:
        db_name: Name of the database file (e.g., 'weather_data_10.db')
    """
    # Check if the database file exists first
    if not os.path.exists(db_name):
        print(f"Error: Database file '{db_name}' not found.")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        print(f"\n{'#' * 80}")
        print(f"#  DATABASE DUMP: {db_name}")
        print(f"{'#' * 80}")

        # Dump all three tables
        log_count = dump_weather_log(cursor)
        graph_count = dump_graph_points(cursor)
        stats_count = dump_stats(cursor)

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"  weather_log:         {log_count:>6} records (raw data)")
        print(f"  weather_graph_points:{graph_count:>6} records (10-min averages)")
        print(f"  weather_stats:       {stats_count:>6} records (global stats)")
        print("=" * 50 + "\n")

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
