#!/bin/bash

# Start the Flask backend in the background
echo "Starting Flask Backend..."
gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 120 run:app &
FLASK_PID=$!

# Start the Streamlit dashboard in the background
# SECURITY: default to binding on localhost only. The dashboard exposes
# aggregate patient prediction data and was previously always bound to
# 0.0.0.0, making it directly reachable by anyone who could reach the
# host's IP (issue #595). Set STREAMLIT_ADDRESS=0.0.0.0 explicitly if this
# is intentionally served through an authenticated reverse proxy.
echo "Starting Streamlit Dashboard..."
STREAMLIT_ADDRESS="${STREAMLIT_ADDRESS:-127.0.0.1}"
streamlit run dashboard.py --server.port 8501 --server.address "$STREAMLIT_ADDRESS" --browser.gatherUsageStats false &
STREAMLIT_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down..."
    kill $FLASK_PID
    kill $STREAMLIT_PID
    exit 0
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Wait for processes
wait $FLASK_PID $STREAMLIT_PID
