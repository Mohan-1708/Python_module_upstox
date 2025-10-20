# # import os
# # from dotenv import load_dotenv
# #
# # # Load environment variables from .env file
# # load_dotenv()
# #
# # # --- API Configuration ---
# # ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
# # if not ACCESS_TOKEN:
# #     raise ValueError("UPSTOX_ACCESS_TOKEN not found in .env file. Please create a .env file.")
# #
# # # --- Database Configuration (NEW) ---
# # DB_HOST = os.getenv("DB_HOST", "localhost")
# # DB_USER = os.getenv("DB_USER", "root")
# # DB_PASSWORD = os.getenv("DB_PASSWORD")
# # DB_NAME = os.getenv("DB_NAME")
# # DB_PORT = os.getenv("DB_PORT", "3306")
# #
# # # Create the database connection string
# # if not DB_PASSWORD or not DB_NAME:
# #     print("Warning: DB_PASSWORD or DB_NAME not set in .env. Database operations will fail.")
# #     DATABASE_URL = None
# # else:
# #     # This is the format for SQLAlchemy: dialect+driver://user:password@host:port/database
# #     DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# #
# #
# # # --- Data Configuration ---
# # STOCKS_CSV_PATH = 'ind_nifty200list.csv'
# # DATA_START_DATE = "2025-09-25"   # Start date for historical data
# # DATA_TIMEZONE = "Asia/Kolkata"
# # DATA_INTERVAL_UNIT = "minutes"
# # DATA_INTERVAL_VALUE = "5"
# #
# # # --- Strategy Parameters ---
# # STRATEGY_NAME = "SMA_VOL_Breakdown"
# # STRATEGY_END_TIME = '11:30'  # Time to stop looking for new signals
# # STOP_LOSS_PCT = 0.012        # 1.2%
# # TAKE_PROFIT_PCT = 0.03         # 3%
# #
# # # --- Output Configuration (UPDATED) ---
# # # We no longer need the CSV path, but we need a table name.
# # RESULTS_DIR = "results" # Still good for logs, etc.
# # DB_TABLE_NAME = f"backtest_results_{STRATEGY_NAME.lower()}"
# #
# # # Ensure the results directory exists (for logs)
# # os.makedirs(RESULTS_DIR, exist_ok=True)
#
#
# import os
# from dotenv import load_dotenv
#
# # Load environment variables from .env file
# load_dotenv()
#
# # --- API Configuration ---
# ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
# if not ACCESS_TOKEN:
#     raise ValueError("UPSTOX_ACCESS_TOKEN not found in .env file. Please create a .env file.")
#
# # --- Database Configuration (NEW) ---
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_USER = os.getenv("DB_USER", "root")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_NAME = os.getenv("DB_NAME")
# DB_PORT = os.getenv("DB_PORT", "3306")
#
# # Create the database connection string
# if not DB_PASSWORD or not DB_NAME:
#     print("Warning: DB_PASSWORD or DB_NAME not set in .env. Database operations will fail.")
#     DATABASE_URL = None
# else:
#     # This is the format for SQLAlchemy: dialect+driver://user:password@host:port/database
#     DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#
#
# # --- Data Configuration ---
# STOCKS_CSV_PATH = 'ind_nifty200list.csv'
#
# DATA_START_DATE = "2025-09-25"   # Start date for historical data
# DATA_TIMEZONE = "Asia/Kolkata"
# DATA_INTERVAL_UNIT = "minutes"
# DATA_INTERVAL_VALUE = "5"
#
# # --- Strategy Parameters ---
# STRATEGY_NAME = "SMA_VOL_Breakdown"
# STRATEGY_END_TIME = '11:30'  # Time to stop looking for new signals
# STOP_LOSS_PCT = 0.012        # 1.2%
# TAKE_PROFIT_PCT = 0.03         # 3%
#
# # --- Output Configuration (UPDATED) ---
# RESULTS_DIR = "results" # For logs
# # NEW: Table for raw candle data
# RAW_DATA_TABLE_NAME = "raw_candle_data"
# # NEW: Table for signals
# SIGNALS_TABLE_NAME = f"generated_signals_{STRATEGY_NAME.lower()}"
# # EXISTING: Table for final backtest P&L
# BACKTEST_TABLE_NAME = f"backtest_results_{STRATEGY_NAME.lower()}"
#
#
# # Ensure the results directory exists (for logs)
# os.makedirs(RESULTS_DIR, exist_ok=True)


import os
from dotenv import load_dotenv
from datetime import datetime, timedelta  # <-- ADD THIS IMPORT

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
if not ACCESS_TOKEN:
    raise ValueError("UPSTOX_ACCESS_TOKEN not found in .env file. Please create a .env file.")

# --- Database Configuration (NEW) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

# Create the database connection string
if not DB_PASSWORD or not DB_NAME:
    print("Warning: DB_PASSWORD or DB_NAME not set in .env. Database operations will fail.")
    DATABASE_URL = None
else:
    # This is the format for SQLAlchemy: dialect+driver://user:password@host:port/database
    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# --- Data Configuration ---
STOCKS_CSV_PATH = 'ind_nifty200list.csv'

# --- DYNAMIC START DATE (UPDATED) ---
# Calculate the start date: 20 days ago from today
DAYS_TO_FETCH = 10
dynamic_start_date = (datetime.now().date() - timedelta(days=DAYS_TO_FETCH))
# Format as "YYYY-MM-DD" string, which the API function expects
DATA_START_DATE = dynamic_start_date.isoformat()
# --- END OF UPDATE ---

DATA_TIMEZONE = "Asia/Kolkata"
DATA_INTERVAL_UNIT = "minutes"
DATA_INTERVAL_VALUE = "5"

# --- Strategy Parameters ---
STRATEGY_NAME = "SMA_VOL_Breakdown"
STRATEGY_END_TIME = '11:30'  # Time to stop looking for new signals
STOP_LOSS_PCT = 0.012        # 1.2%
TAKE_PROFIT_PCT = 0.03         # 3%

# --- Output Configuration (UPDATED) ---
RESULTS_DIR = "results" # For logs
# NEW: Table for raw candle data
RAW_DATA_TABLE_NAME = "raw_candle_data"
# NEW: Table for signals
SIGNALS_TABLE_NAME = f"generated_signals_{STRATEGY_NAME.lower()}"
# EXISTING: Table for final backtest P&L
BACKTEST_TABLE_NAME = f"backtest_results_{STRATEGY_NAME.lower()}"


# Ensure the results directory exists (for logs)
os.makedirs(RESULTS_DIR, exist_ok=True)