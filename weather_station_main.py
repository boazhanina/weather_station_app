import time
import weather_station_config as config
import weather_station_func as func
import weather_station_sql as sql
import sqlite3
import pandas as pd

def get_global_stats():
    """Calculates the absolute Minimum and Maximum from all 5 sensors across the entire database."""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        # Querying the Min and Max across all 5 temperature columns
        query = """
            SELECT 
                MIN(min_val) as global_min,
                MAX(max_val) as global_max
            FROM (
                SELECT MIN(temp_0) as min_val, MAX(temp_0) as max_val FROM weather_log
                UNION ALL
                SELECT MIN(temp_1), MAX(temp_1) FROM weather_log
                UNION ALL
                SELECT MIN(temp_2), MAX(temp_2) FROM weather_log
                UNION ALL
                SELECT MIN(temp_3), MAX(temp_3) FROM weather_log
                UNION ALL
                SELECT MIN(temp_4), MAX(temp_4) FROM weather_log
            )
        """
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
    # Updated Header for 5 sensors
    print("\n" + "="*120)
    print(f"{'DATE':<12} | {'TIME':<10} | {'T0':>7} | {'T1':>7} | {'T2':>7} | {'T3':>7} | {'T4':>7} | {'MIN':>7} | {'MAX':>7} | {'CPU':>6}")
    print("-" * 120)

    try:
        while True:
            if config.LOW_POWER_MODE:
                func.set_power_state(True)

            # 1. READ DATA FROM ALL 5 SENSORS
            temperatures = func.get_ambient_temp()
            cpu_temp = func.get_cpu_temp()
            curr_date = time.strftime("%Y-%m-%d")
            curr_time = time.strftime("%H:%M:%S")

            # Check if we got at least one valid reading
            valid_temps = [t for t in temperatures.values() if t is not None]
            
            if valid_temps:
                # 2. SAVE TO DATABASE
                sql.save_reading(curr_date, curr_time, temperatures, cpu_temp)
                
                # 3. CALCULATE GLOBAL STATS
                global_min, global_max = get_global_stats()
                
                # 4. PREPARE OUTPUT
                reset = func.get_reset_code()
                
                # Format temperature strings with colors
                temp_strs = []
                for i in range(5):
                    temp = temperatures.get(i)
                    if temp is not None:
                        color = func.get_color_code(temp)
                        temp_strs.append(f"{color}{temp:>6.1f}{reset}")
                    else:
                        temp_strs.append(f"{'N/A':>6}")
                
                # Format: Date | Time | T0 | T1 | T2 | T3 | T4 | Min | Max | CPU
                print(f"{curr_date:<12} | {curr_time:<10} | "
                      f"{temp_strs[0]}° | {temp_strs[1]}° | {temp_strs[2]}° | {temp_strs[3]}° | {temp_strs[4]}° | "
                      f"{global_min:>6.1f}° | {global_max:>6.1f}° | "
                      f"{cpu_temp:>5.1f}°")

            if config.LOW_POWER_MODE:
                time.sleep(config.SYNC_WINDOW)
                print("--- Low Power: Disconnecting WiFi ---")
                func.set_power_state(False)
            
            time.sleep(config.SLEEP_TIME)

    except KeyboardInterrupt:
        func.set_power_state(True)
        print("\n" + "="*120)
        print("Station stopped by user.")

if __name__ == "__main__":
    main()
