import pandas as pd
from datetime import datetime
import logging

def backtest_strategy_combined(signals_df: pd.DataFrame, all_stocks_data: dict) -> pd.DataFrame:
    """
    Backtests the trading strategy using combined signals across all stocks.
    """
    trade_results = []

    if signals_df.empty:
        logging.warning("No trading signals generated. Skipping backtesting.")
        return pd.DataFrame(columns=['Symbol', 'Signal_Timestamp', 'Entry_Price', 'Stop_Loss', 'Take_Profit', 'Exit_Timestamp', 'Exit_Price', 'Outcome', 'Profit_Loss'])

    # Sort signals by timestamp to simulate chronological execution
    signals_df = signals_df.sort_values(by='Signal_Timestamp')

    for index, signal_row in signals_df.iterrows():
        symbol = signal_row['Symbol']
        signal_timestamp = signal_row['Signal_Timestamp']
        entry_price = signal_row['Entry_Price']
        stop_loss_price = signal_row['Stop_Loss']
        take_profit_price = signal_row['Take_Profit']

        df = all_stocks_data.get(symbol)

        if df is None or df.empty:
            logging.warning(f"Skipping backtest for signal on {symbol}: Data not found or empty.")
            continue

        try:
            signal_loc = df.index.get_loc(signal_timestamp)
        except KeyError:
            logging.warning(f"Signal timestamp {signal_timestamp} not found in data for {symbol}. Skipping.")
            continue

        trade_date = signal_timestamp.date()
        end_of_day = datetime.combine(trade_date, datetime.strptime('15:30', '%H:%M').time()).replace(tzinfo=signal_timestamp.tzinfo)

        trade_outcome = "Open"
        exit_price = None
        exit_timestamp = None
        profit_loss = None

        start_sim_loc = signal_loc + 1 # Start simulation from the *next* candle

        for i in range(start_sim_loc, len(df)):
            current_candle = df.iloc[i]
            current_timestamp = df.index[i]

            # 1. Check for End of Day
            if current_timestamp > end_of_day:
                trade_outcome = "Open (Closed EOD)"
                # Exit at the close of the *last valid candle* of the day
                eod_candles = df.loc[(df.index.date == trade_date) & (df.index <= end_of_day)]
                if not eod_candles.empty:
                    last_eod_candle = eod_candles.iloc[-1]
                    exit_price = last_eod_candle['close']
                    exit_timestamp = last_eod_candle.name
                    profit_loss = entry_price - exit_price # Sell trade: Entry - Exit
                else:
                    # Fallback if something is wrong
                    exit_price = df.iloc[signal_loc]['close']
                    exit_timestamp = signal_timestamp
                    profit_loss = entry_price - exit_price
                    trade_outcome = "Open (Closed Signal Candle)"
                break

                # 2. Check for Stop Loss (Sell trade)
            if current_candle['high'] >= stop_loss_price:
                trade_outcome = "Loss"
                exit_price = stop_loss_price # Exit at stop loss price
                exit_timestamp = current_timestamp
                profit_loss = entry_price - exit_price
                break

                # 3. Check for Take Profit (Sell trade)
            if current_candle['low'] <= take_profit_price:
                trade_outcome = "Win"
                exit_price = take_profit_price # Exit at take profit price
                exit_timestamp = current_timestamp
                profit_loss = entry_price - exit_price
                break

                # If loop finishes without exit, it's an open trade closed at last available data
        if trade_outcome == "Open":
            last_candle = df.iloc[-1]
            exit_price = last_candle['close']
            exit_timestamp = df.index[-1]
            profit_loss = entry_price - exit_price
            trade_outcome = "Open (Closed Last Data)"

        trade_results.append({
            'Symbol': symbol,
            'Signal_Timestamp': signal_timestamp,
            'Entry_Price': entry_price,
            'Stop_Loss': stop_loss_price,
            'Take_Profit': take_profit_price,
            'Exit_Timestamp': exit_timestamp,
            'Exit_Price': exit_price,
            'Outcome': trade_outcome,
            'Profit_Loss': profit_loss
        })

    return pd.DataFrame(trade_results)