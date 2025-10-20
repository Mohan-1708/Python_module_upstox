import logging
import sys
import pandas as pd
from sqlalchemy import create_engine, text

def setup_logging():
    """Configures a basic logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("backtest.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_stocks_list(filepath: str) -> pd.DataFrame:
    """Loads the list of stocks from a CSV file."""
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        logging.error(f"Stock list file not found at: {filepath}")
        sys.exit(1) # Exit if we can't load stocks

def get_db_engine(db_url: str):
    """Creates and returns a SQLAlchemy engine."""
    if not db_url:
        logging.error("DATABASE_URL is not configured in .env. Cannot connect to database.")
        return None
    try:
        return create_engine(db_url)
    except Exception as e:
        logging.error(f"Failed to create database engine: {e}")
        return None

def save_candle_data_to_db(df: pd.DataFrame, engine, table_name: str):
    """
    Saves the combined raw candle data DataFrame to the database.
    This function will RESET the index to save 'timestamp' as a column.
    """
    if engine is None:
        return

    try:
        # Reset index to make 'timestamp' a regular column for SQL
        df_to_save = df.reset_index()

        # Add a 'Symbol' column if it's not already present (from a combined df)
        # Note: The new main.py will add this, but this is a safeguard.
        if 'Symbol' not in df_to_save.columns and 'Symbol' in df_to_save.columns:
             df_to_save['Symbol'] = df_to_save['Symbol']

        logging.info(f"Saving {len(df_to_save)} rows of candle data to table: {table_name}...")

        # Use if_exists='replace' to do a full refresh every time.
        df_to_save.to_sql(table_name, con=engine, if_exists='replace', index=False)

        logging.info(f"Successfully saved raw candle data to {table_name}.")

        # Optional: Add an index on Symbol and timestamp for faster queries
        with engine.connect() as conn:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON {table_name} (Symbol, timestamp)"))
            conn.commit()
        logging.info("Database index created on (Symbol, timestamp).")

    except Exception as e:
        logging.error(f"Failed to save raw candle data to database: {e}")

def load_data_from_db(engine, table_name: str) -> pd.DataFrame:
    """
    Loads all candle data from the database.
    Converts 'timestamp' back to a datetime index.
    """
    if engine is None:
        return pd.DataFrame()

    try:
        logging.info(f"Loading raw candle data from table: {table_name}...")
        df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)

        if df.empty:
            logging.warning(f"No data found in table {table_name}.")
            return pd.DataFrame()

        # Crucial: Convert timestamp column back to datetime and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()

        logging.info(f"Successfully loaded {len(df)} rows from {table_name}.")
        return df

    except Exception as e:
        logging.error(f"Failed to load raw data from database: {e}")
        return pd.DataFrame()

def save_results_to_db(df: pd.DataFrame, engine, table_name: str):
    """
    Saves a results (signals or backtest) DataFrame to a SQL database table.
    """
    if engine is None:
        logging.error("Database engine is not available. Cannot save results.")
        return

    try:
        # Use if_exists='replace' to overwrite old results
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        logging.info(f"Successfully saved results to database table: {table_name}")

    except Exception as e:
        # This will catch connection errors, auth errors, etc.
        logging.error(f"Failed to save results to {table_name}: {e}")