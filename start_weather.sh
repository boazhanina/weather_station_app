#!/bin/bash
# Clean startup script for weather station and Flask dashboard
# Updated to show the Flask dashboard URL at the end

PROJECT_DIR="/home/hanina/weather_app_latest"
DB_PATH="$PROJECT_DIR/weather_data_10.db"
FLASK_PORT=5000

echo "Stopping existing weather station processes..."
pkill -f weather_station_main.py
pkill -f weather_flask_app.py

# Give the system a moment to release resources
sleep 2

echo "Starting weather station main process..."
cd "$PROJECT_DIR"
nohup python3.9 weather_station_main.py >> "$PROJECT_DIR/app_debug.log" 2>&1 &


# Wait until database exists and has at least one record
echo "Waiting for database to be ready..."
until [ -f "$DB_PATH" ] && sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM weather_log;" | grep -q -v '^0$'; do
    sleep 2
done

echo "Starting Flask dashboard..."
nohup python3.9 weather_flask_app.py >> "$PROJECT_DIR/app_debug.log" 2>&1 &

# Get the local IP address of the Pi
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "----------------------------------------------------"
echo "Flask dashboard should be available at:"
echo "http://$LOCAL_IP:$FLASK_PORT"
echo "Open this URL in your browser on the same network."
echo "----------------------------------------------------"

