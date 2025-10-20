import pandas as pd
import upstox_client
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # if needed

# ------------- API Client Setup -------------
def get_api_client(access_token: str) -> upstox_client.HistoryV3Api:
    """Configures and returns the Upstox History API client."""
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_client = upstox_client.ApiClient(configuration)
    return upstox_client.HistoryV3Api(api_client)

# ------------- Helpers (response -> DataFrame) -------------
def _extract_candles(resp):
    """Safely get the candles list from SDK response or dict."""
    try:
        candles = getattr(getattr(resp, "data", None), "candles", None)
        if candles is not None:
            return candles
    except Exception:
        pass
    if isinstance(resp, dict):
        return resp.get("data", {}).get("candles", []) or []
    try:
        return resp["data"]["candles"]
    except Exception:
        return []

def candles_to_df(candles):
    """Convert Upstox candle array -> tidy DataFrame indexed by timestamp."""
    if not candles:
        return pd.DataFrame(columns=["open","high","low","close","volume","open_interest"])
    base_cols = ["timestamp","open","high","low","close","volume","open_interest"]
    cols = base_cols[:len(candles[0])]
    df = pd.DataFrame(candles, columns=cols)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)  # keeps "+05:30" if present
    df = df.sort_values("timestamp").set_index("timestamp")
    for c in ["open","high","low","close","volume","open_interest"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "open_interest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["open_interest"], errors="coerce")
    return df

def fetch_historical_df(api, instrument_key, unit, interval, to_date, from_date=None):
    """Historical V3 wrapper (handles both with/without from_date)."""
    if from_date:
        resp = api.get_historical_candle_data1(instrument_key, unit, interval, to_date, from_date)
    else:
        resp = api.get_historical_candle_data(instrument_key, unit, interval, to_date)
    return candles_to_df(_extract_candles(resp))

def fetch_intraday_df(api, instrument_key, unit="minutes", interval="1"):
    """Intraday V3 wrapper (current trading day only)."""
    resp = api.get_intra_day_candle_data(instrument_key, unit, interval)
    return candles_to_df(_extract_candles(resp))

# ------------- Main: combine Historical (till yesterday) + Intraday (today) -------------
def get_continuous_candles(api: upstox_client.HistoryV3Api,
                           instrument_key: str,
                           unit: str,
                           interval: str,
                           from_date: str,
                           tz: str) -> pd.DataFrame:
    """
    Returns a single, continuous DataFrame of candles from `from_date` up to 'now',
    by stitching Historical V3 (<= yesterday) with Intraday V3 (today).
    """
    today = datetime.now(ZoneInfo(tz)).date()
    yday = today - timedelta(days=1)

    frames = []

    # 1) Historical up to yesterday (only if the window is valid)
    start = datetime.fromisoformat(from_date).date()
    if start <= yday:
        df_hist = fetch_historical_df(
            api,
            instrument_key=instrument_key,
            unit=unit,
            interval=interval,
            from_date=start.isoformat(),
            to_date=yday.isoformat()
        )
        frames.append(df_hist)

    # 2) Intraday for today
    df_id = fetch_intraday_df(api, instrument_key, unit=unit, interval=interval)
    if not df_id.empty:
        df_id = df_id.loc[df_id.index.date == today]  # keep only today's rows
        frames.append(df_id)

    # 3) Concatenate, sort, and de-duplicate (prefer later rows -> intraday overwrites)
    if frames:
        df = pd.concat(frames)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        # Normalize columns if OI present in one and not the other
        for col in ["open_interest"]:
            if col not in df.columns:
                df[col] = pd.NA
        return df[["open","high","low","close","volume","open_interest"]]
    else:
        # No data (e.g., future start date or holiday + no history yet)
        return pd.DataFrame(columns=["open","high","low","close","volume","open_interest"])