import time
import weather_station_config as config
import weather_station_func as func
import weather_station_sql as sql
import sqlite3
import pandas as pd

def get_global_stats():
    """Calculates the absolute Minimum and Maximum from the entire database."""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        # Querying the Min and Max of all time
        query = "SELECT MIN(ambient_temp), MAX(ambient_temp) FROM weather_log"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        g_min = df.iloc[0, 0]
        g_max = df.iloc[0, 1]

        # Return 0.0 if None (for an empty database)
        return (g_min if g_min is not None else 0.0), (g_max if g_max is not None else 0.0)
    except Exception:
        return 0.0, 0.0

def main():
    sql.init_db()
    # Updated Header
    print("\n" + "="*85)
    print(f"{'DATE':<12} | {'TIME':<10} | {'CURRENT':<8} | {'GLOBAL MIN':<12} | {'GLOBAL MAX':<12} | {'CPU'}")
    print("-" * 85)

    try:
        while True:
            if config.LOW_POWER_MODE:
                func.set_power_state(True)

            # 1. READ DATA
            amb_temp = func.get_ambient_temp()
            cpu_temp = func.get_cpu_temp()
            curr_date = time.strftime("%Y-%m-%d")
            curr_time = time.strftime("%H:%M:%S")

            if amb_temp is not None:
                # 2. SAVE TO DATABASE
                sql.save_reading(curr_date, curr_time, amb_temp, cpu_temp)
                
                # 3. CALCULATE GLOBAL STATS
                global_min, global_max = get_global_stats()
                
                # 4. PREPARE COLORS & PRINT
                color = func.get_color_code(amb_temp)
                reset = func.get_reset_code()
                
                # Format: Date | Time | Current | Global Min | Global Max | CPU
                print(f"{curr_date:<12} | {curr_time:<10} | "
                      f"{color}{amb_temp:>6.2f}°C{reset} | "
                      f"{global_min:>10.2f}°C  | "
                      f"{global_max:>10.2f}°C  | "
                      f"{cpu_temp:.1f}°C")

            if config.LOW_POWER_MODE:
                time.sleep(config.SYNC_WINDOW)
                print("--- Low Power: Disconnecting WiFi ---")
                func.set_power_state(False)
            
            time.sleep(config.SLEEP_TIME)

    except KeyboardInterrupt:
        func.set_power_state(True)
        print("\n" + "="*85)
        print("Station stopped by user.")

if __name__ == "__main__":
    main()
