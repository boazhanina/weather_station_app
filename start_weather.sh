#!/bin/bash
# Clean startup script for weather station and Flask dashboard
# Updated to support Cloudflare Tunnel for external access

PROJECT_DIR="/home/hanina/weather_app"
DB_PATH="$PROJECT_DIR/weather_data_10.db"
FLASK_PORT=5000
CLOUDFLARE_URL="https://haninas.com"

echo "=============================================="
echo "  Weather Station Startup Script"
echo "=============================================="

echo ""
echo "[1/5] Stopping existing weather station processes..."
pkill -f weather_station_main.py
pkill -f weather_flask_app.py

# Give the system a moment to release resources
sleep 2

echo "[2/5] Starting weather station main process..."
cd "$PROJECT_DIR"
nohup python3 weather_station_main.py >> "$PROJECT_DIR/app_debug.log" 2>&1 &

# Wait until database exists and has at least one record
echo "[3/5] Waiting for database to be ready..."
until [ -f "$DB_PATH" ] && sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM weather_log;" 2>/dev/null | grep -q -v '^0$'; do
    sleep 2
done
echo "      Database ready!"

echo "[4/5] Starting Flask dashboard..."
nohup python3 weather_flask_app.py >> "$PROJECT_DIR/app_debug.log" 2>&1 &
sleep 2

echo "[5/5] Checking Cloudflare Tunnel..."
sudo systemctl restart cloudflared
sleep 3

# Check if cloudflared is running
if systemctl is-active --quiet cloudflared; then
    TUNNEL_STATUS="✓ Connected"
else
    TUNNEL_STATUS="✗ Not connected (check: sudo systemctl status cloudflared)"
fi

# Get the local IP address of the Pi
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=============================================="
echo "  Weather Station Started Successfully!"
echo "=============================================="
echo ""
echo "  Local Access (same WiFi):"
echo "    http://$LOCAL_IP:$FLASK_PORT"
echo ""
echo "  External Access (anywhere):"
echo "    $CLOUDFLARE_URL"
echo "    Tunnel Status: $TUNNEL_STATUS"
echo ""
echo "=============================================="

