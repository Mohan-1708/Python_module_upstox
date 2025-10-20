import pandas as pd
from datetime import datetime
import logging

def generate_signals(df: pd.DataFrame,
                     stock_symbol: str,
                     end_time_str: str,
                     stop_loss_pct: float,
                     take_profit_pct: float) -> list:
    """
    Applies the SMA/Volume breakdown strategy to a single stock's DataFrame.
    Returns a list of signal dictionaries.
    """

    if df.empty:
        return []

    signals = []

    # Calculate indicators
    df["SMA_5"] = df["close"].rolling(window=5).mean()
    df["VOL_100"] = df["volume"].rolling(window=100).mean()

    # Apply strategy only to data up to the specified time
    strategy_time_limit = datetime.strptime(end_time_str, '%H:%M').time()
    df_strategy = df[df.index.time <= strategy_time_limit].copy()

    # Condition 1: Candle low > SMA_5 and Volume > 5 * VOL_100
    condition1 = (df_strategy['low'] > df_strategy['SMA_5']) & \
                 (df_strategy['volume'] > 5 * df_strategy['VOL_100'])

    condition1_indices = df_strategy.index[condition1]

    # Condition 2: When the next candle breaks the low of the Condition 1 candle.
    for i in condition1_indices:
        try:
            next_candle_index_loc = df.index.get_loc(i) + 1
            if next_candle_index_loc < len(df):
                next_candle_index = df.index[next_candle_index_loc]

                # Ensure next candle is on the same day
                if next_candle_index.date() != i.date():
                    continue

                if df.loc[next_candle_index, 'low'] < df.loc[i, 'low']:
                    # Sell signal triggered
                    entry_price = df.loc[i]['low'] # Entry is the low of the condition 1 candle
                    stop_loss_price = entry_price * (1 + stop_loss_pct)
                    take_profit_price = entry_price * (1 - take_profit_pct)

                    signals.append({
                        'Symbol': stock_symbol,
                        'Signal': 'Sell',
                        'Signal_Timestamp': next_candle_index,
                        'Entry_Price': entry_price,
                        'Stop_Loss': stop_loss_price,
                        'Take_Profit': take_profit_price
                    })

        except KeyError:
            logging.warning(f"Timestamp {i} not found in original dataframe for {stock_symbol}")
            pass
        except Exception as e:
            logging.error(f"Error processing signal for {stock_symbol} at {i}: {e}")

    return signals