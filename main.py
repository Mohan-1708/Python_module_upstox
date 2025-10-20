import pandas as pd
import logging

# Import from our config and modules
import config
from src.utils import (
    setup_logging,
    load_stocks_list,
    get_db_engine,
    save_candle_data_to_db,
    load_data_from_db,
    save_results_to_db
)
from src.data_fetcher import get_api_client, get_continuous_candles
from src.strategy import generate_signals
from src.backtester import backtest_strategy_combined

def main():
    """
    Main function to run the full pipeline:
    1. Fetch all stock data and save to DB.
    2. Load data from DB, generate signals, and save signals to DB.
    3. Run backtest on signals and save results to DB.
    """
    setup_logging()
    logging.info(f"Starting full backtest pipeline for: {config.STRATEGY_NAME}")

    # 1. Load Stocks
    logging.info(f"Loading stock list from: {config.STOCKS_CSV_PATH}")
    stocks_df = load_stocks_list(config.STOCKS_CSV_PATH)

    # 2. Initialize API and DB Clients
    try:
        api = get_api_client(config.ACCESS_TOKEN)
    except Exception as e:
        logging.error(f"Failed to initialize API client: {e}")
        return

    db_engine = get_db_engine(config.DATABASE_URL)
    if db_engine is None:
        logging.error("Failed to initialize DB engine. Exiting.")
        return

    # =========================================================================
    # STAGE 1: FETCH DATA AND SAVE TO DATABASE
    # =========================================================================
    logging.info(f"--- STAGE 1: Fetching Data for {len(stocks_df)} stocks ---")

    all_stocks_data_frames = [] # To store individual DFs before combining

    for index, row in stocks_df.iterrows():
        stock_symbol = row['Symbol']
        instrument_key = f"NSE_EQ|{row['ISIN Code']}"
        logging.info(f"Fetching: {stock_symbol} ({instrument_key})")

        try:
            df_5m = get_continuous_candles(
                api=api,
                instrument_key=instrument_key,
                unit=config.DATA_INTERVAL_UNIT,
                interval=config.DATA_INTERVAL_VALUE,
                from_date=config.DATA_START_DATE,
                tz=config.DATA_TIMEZONE
            )

            if not df_5m.empty:
                # IMPORTANT: Add the symbol to the dataframe
                df_5m['Symbol'] = stock_symbol
                all_stocks_data_frames.append(df_5m)
            else:
                logging.warning(f"No data fetched for {stock_symbol}.")

        except Exception as e:
            logging.error(f"Error fetching data for {stock_symbol}: {e}", exc_info=True)

    if not all_stocks_data_frames:
        logging.error("No data fetched for any stock. Exiting.")
        return

    # Combine all individual dataframes into one large one
    combined_raw_data_df = pd.concat(all_stocks_data_frames)

    # Save the combined dataframe to the database
    save_candle_data_to_db(combined_raw_data_df, db_engine, config.RAW_DATA_TABLE_NAME)

    # =========================================================================
    # STAGE 2: LOAD DATA, RUN STRATEGY, AND SAVE SIGNALS
    # =========================================================================
    logging.info(f"--- STAGE 2: Loading Data from DB and Generating Signals ---")

    # Load all data back from the DB
    # This proves Stage 1 worked and decouples the logic
    all_data_from_db = load_data_from_db(db_engine, config.RAW_DATA_TABLE_NAME)

    if all_data_from_db.empty:
        logging.error("Failed to load data from database. Cannot run strategy. Exiting.")
        return

    # Re-create the dictionary structure needed for the backtester
    # This groups the big DataFrame by 'Symbol'
    all_stocks_data_dict = {}
    for symbol, group_df in all_data_from_db.groupby('Symbol'):
        # Drop the 'Symbol' column as the strategy functions don't need it
        all_stocks_data_dict[symbol] = group_df.drop(columns=['Symbol'])

    all_combined_signals = []

    logging.info(f"Running strategy for {len(all_stocks_data_dict)} stocks...")
    for stock_symbol, stock_df in all_stocks_data_dict.items():
        try:
            stock_signals = generate_signals(
                df=stock_df,
                stock_symbol=stock_symbol,
                end_time_str=config.STRATEGY_END_TIME,
                stop_loss_pct=config.STOP_LOSS_PCT,
                take_profit_pct=config.TAKE_PROFIT_PCT
            )

            if stock_signals:
                logging.info(f"Found {len(stock_signals)} signals for {stock_symbol}.")
                all_combined_signals.extend(stock_signals)
        except Exception as e:
            logging.error(f"Error running strategy for {stock_symbol}: {e}", exc_info=True)

    if not all_combined_signals:
        logging.warning("No signals generated for any stock. Backtest will be skipped.")
        all_combined_signals_df = pd.DataFrame()
    else:
        all_combined_signals_df = pd.DataFrame(all_combined_signals)

    # Save the generated signals to their own table
    logging.info(f"Total signals generated: {len(all_combined_signals_df)}")
    save_results_to_db(all_combined_signals_df, db_engine, config.SIGNALS_TABLE_NAME)

    # =========================================================================
    # STAGE 3: RUN BACKTEST AND SAVE RESULTS
    # =========================================================================
    if all_combined_signals_df.empty:
        logging.info("--- STAGE 3: Skipped Backtesting (No Signals) ---")
        logging.info("Backtest run finished.")
        return

    logging.info(f"--- STAGE 3: Running Backtest on {len(all_combined_signals_df)} Signals ---")

    backtest_results_df = backtest_strategy_combined(
        all_combined_signals_df,
        all_stocks_data_dict
    )

    # 5. Summarize and Save Final Results
    if not backtest_results_df.empty:
        overall_profit_loss = backtest_results_df['Profit_Loss'].sum()
        total_trades = len(backtest_results_df)
        wins = len(backtest_results_df[backtest_results_df['Outcome'] == 'Win'])
        losses = len(backtest_results_df[backtest_results_df['Outcome'] == 'Loss'])
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        logging.info("--- Backtest Summary ---")
        logging.info(f"Total Trades: {total_trades}")
        logging.info(f"Wins: {wins} | Losses: {losses}")
        logging.info(f"Win Rate: {win_rate:.2f}%")
        logging.info(f"Overall Profit/Loss: {overall_profit_loss:.2f}")

        # Save the final backtest results
        save_results_to_db(
            df=backtest_results_df,
            engine=db_engine,
            table_name=config.BACKTEST_TABLE_NAME
        )
    else:
        logging.warning("Backtest completed but produced no results.")

    logging.info("Backtest run finished.")

if __name__ == "__main__":
    main()