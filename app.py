import sys
import subprocess
import threading
import logging
from flask import Flask, jsonify

# --- Configuration ---
# Set up logging to see server and script status
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[
        logging.FileHandler("app_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)
is_backtest_running = False
backtest_lock = threading.Lock()

# --- Background Task ---
def run_backtest_script():
    """
    Runs the main.py script in a separate process.
    This function is designed to be run in a background thread.
    """
    global is_backtest_running

    # Use sys.executable to ensure it uses the same Python interpreter
    # that is running the Flask app.
    try:
        logging.info("Backtest script started...")
        # This will run 'python main.py'
        subprocess.run(
            [sys.executable, 'main.py'],
            check=True,         # Will raise an error if main.py fails
            capture_output=True, # Captures stdout and stderr
            text=True
        )
        logging.info("Backtest script finished successfully.")
    except subprocess.CalledProcessError as e:
        # This logs any error that main.py might have thrown
        logging.error(f"Backtest script failed with error:\n{e.stderr}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while running script: {e}")
    finally:
        # Use the lock to safely update the shared variable
        with backtest_lock:
            is_backtest_running = False
            logging.info("Backtest status set to 'not running'.")


# --- API Endpoint ---
@app.route('/start', methods=['POST', 'GET'])
def start_backtest():
    """
    API endpoint to trigger the backtest.
    """
    global is_backtest_running

    # Check if a backtest is already in progress
    with backtest_lock:
        if is_backtest_running:
            logging.warning("Received /start request, but backtest is already running.")
            # Return a "Conflict" status
            return jsonify({
                "status": "error",
                "message": "Backtest is already in progress."
            }), 409

        # If not running, set the flag and start the thread
        is_backtest_running = True
        logging.info("Received /start request. Starting backtest in background thread...")

        # Start the backtest in a new thread.
        # This allows us to return an HTTP response immediately
        # without waiting for the (potentially long) backtest to finish.
        thread = threading.Thread(target=run_backtest_script, name="BacktestRunner")
        thread.start()

    # Return an "Accepted" status, indicating the job has started
    return jsonify({
        "status": "success",
        "message": "Backtest started in the background. Check logs for progress."
    }), 202

@app.route('/status', methods=['GET'])
def get_status():
    """
    API endpoint to check if a backtest is currently running.
    """
    with backtest_lock:
        if is_backtest_running:
            return jsonify({"status": "running", "message": "A backtest is currently in progress."})
        else:
            return jsonify({"status": "idle", "message": "No backtest is running."})

# --- Run the Server ---
if __name__ == '__main__':
    logging.info(f"Starting web server. Access on http://<your_ip>:8080")

    # Set host='0.0.0.0' to make the server accessible
    # from your network IP (e.g., 192.168.0.1)
    # and not just from 'localhost'.
    app.run(host='0.0.0.0', port=8080, debug=False)