#!/bin/bash

# Start the Flask backend in the background
echo "Starting Flask Backend..."
gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 120 run:app &
FLASK_PID=$!

# Start the Streamlit dashboard in the background
echo "Starting Streamlit Dashboard..."
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false &
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
