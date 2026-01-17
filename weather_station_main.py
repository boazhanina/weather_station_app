import time
import weather_station_config as config
import weather_station_func as func
import weather_station_sql as sql

# Buffer to store minute readings for 10-minute calculation
minute_buffer = []

def calculate_minute_value(temperatures):
    """
    Calculate per-minute value: average of the 2 middle values from sensors 0-3.
    
    Args:
        temperatures: Dictionary with sensor_index as key and temperature as value
        
    Returns:
        Calculated value or None if not enough valid readings
    """
    # Get valid readings from sensors 0-3 only
    temps = [temperatures.get(i) for i in range(4) if temperatures.get(i) is not None]
    
    if len(temps) < 2:
        return None
    
    # Sort and take the 2 middle values
    temps_sorted = sorted(temps)
    if len(temps_sorted) == 2:
        middle_two = temps_sorted
    elif len(temps_sorted) == 3:
        # Just the middle one
        return temps_sorted[1]
    else:  # 4 values
        middle_two = temps_sorted[1:3]  # The 2 middle values
    
    return sum(middle_two) / len(middle_two)

def process_10_minute_bucket(buffer, curr_date, curr_time):
    """
    Process 10 readings to create a single graph point.
    
    Args:
        buffer: List of minute values
        curr_date: Current date string
        curr_time: Current time string (will use HH:MM format)
    """
    valid_values = [v for v in buffer if v is not None]
    
    if valid_values:
        # Calculate average of the 10-minute bucket
        avg_value = round(sum(valid_values) / len(valid_values), 2)
        time_label = curr_time[:5]  # HH:MM format
        
        # Save to graph points table
        sql.save_graph_point(curr_date, time_label, avg_value)
        
        # Update global stats (checks if this beats current max/min)
        sql.update_global_stats(avg_value, curr_date, time_label)
        
        print(f"  >>> 10-min graph point saved: {avg_value}°C at {time_label}")
        return avg_value
    
    return None

def main():
    global minute_buffer
    
    sql.init_db()
    
    # Get current global stats for display
    stats = sql.get_global_stats()
    
    # Updated Header for 5 sensors
    print("\n" + "="*130)
    print(f"{'DATE':<12} | {'TIME':<10} | {'T0':>7} | {'T1':>7} | {'T2':>7} | {'T3':>7} | {'T4':>7} | {'CALC':>7} | {'G_MIN':>7} | {'G_MAX':>7} | {'CPU':>6}")
    print("-" * 130)

    reading_count = 0  # Counter for 10-minute buckets

    try:
        while True:
            if config.LOW_POWER_MODE:
                func.set_power_state(True)

            # 1. READ DATA FROM ALL 5 SENSORS
            temperatures = func.get_ambient_temp()
            cpu_temp = func.get_cpu_temp()
            curr_date = time.strftime("%Y-%m-%d")
            curr_time = time.strftime("%H:%M:%S")

            # Check if we got at least one valid reading from sensors 0-3
            valid_temps = [temperatures.get(i) for i in range(4) if temperatures.get(i) is not None]
            
            if valid_temps:
                # 2. SAVE RAW READING TO DATABASE
                sql.save_reading(curr_date, curr_time, temperatures, cpu_temp)
                
                # 3. CALCULATE PER-MINUTE VALUE (average of 2 middle sensors)
                minute_value = calculate_minute_value(temperatures)
                minute_buffer.append(minute_value)
                reading_count += 1
                
                # 4. EVERY 10 READINGS, CREATE A GRAPH POINT
                if reading_count >= 10:
                    process_10_minute_bucket(minute_buffer, curr_date, curr_time)
                    minute_buffer = []  # Reset buffer
                    reading_count = 0
                    # Refresh global stats after update
                    stats = sql.get_global_stats()
                
                # 5. PREPARE OUTPUT
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
                
                # Format minute value
                calc_str = f"{minute_value:>6.1f}" if minute_value is not None else "  N/A "
                
                # Get global min/max from stats
                g_min = stats['min']['value'] if stats['min']['value'] is not None else 0.0
                g_max = stats['max']['value'] if stats['max']['value'] is not None else 0.0
                
                # Format: Date | Time | T0 | T1 | T2 | T3 | T4 | Calc | G_Min | G_Max | CPU
                print(f"{curr_date:<12} | {curr_time:<10} | "
                      f"{temp_strs[0]}° | {temp_strs[1]}° | {temp_strs[2]}° | {temp_strs[3]}° | {temp_strs[4]}° | "
                      f"{calc_str}° | {g_min:>6.1f}° | {g_max:>6.1f}° | "
                      f"{cpu_temp:>5.1f}°")

            if config.LOW_POWER_MODE:
                time.sleep(config.SYNC_WINDOW)
                print("--- Low Power: Disconnecting WiFi ---")
                func.set_power_state(False)
            
            time.sleep(config.SLEEP_TIME)

    except KeyboardInterrupt:
        func.set_power_state(True)
        print("\n" + "="*130)
        print("Station stopped by user.")

if __name__ == "__main__":
    main()
