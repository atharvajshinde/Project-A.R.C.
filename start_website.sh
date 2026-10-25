#!/usr/bin/env bash
# ==============================================================================
# PROJECT A.R.C. — Presentation & Web Experience Launcher
# ==============================================================================

set -e

# Always run from the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=8080

echo "--------------------------------------------------"
echo "  PROJECT A.R.C. // Autonomous PV Maintenance Robot"
echo "  Digital Twin & Judge Defense Presentation Server"
echo "--------------------------------------------------"

# Check if port 8080 is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Notice: Port $PORT is already active and serving."
else
    echo "Starting Python HTTP Server on port $PORT..."
    python3 -m http.server $PORT &
    SERVER_PID=$!
    sleep 0.8
fi

# Detect Network IP for tablet / phone access during live demonstrations
LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo ""
echo "🚀 Web portal is ready:"
echo "   • Localhost:       http://localhost:$PORT/"
echo "   • Direct Web View: http://localhost:$PORT/web/"
if [ "$LAN_IP" != "localhost" ] && [ -n "$LAN_IP" ]; then
    echo "   • Network/Mobile:  http://$LAN_IP:$PORT/web/"
fi
echo ""
echo "Press Ctrl+C to stop the server when finished."
echo "--------------------------------------------------"

# Automatically open in default browser if in desktop session
if command -v xdg-open >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    xdg-open "http://localhost:$PORT/web/" >/dev/null 2>&1 &
fi

# Keep script alive if we spawned the background server
if [ -n "$SERVER_PID" ]; then
    wait $SERVER_PID
fi
