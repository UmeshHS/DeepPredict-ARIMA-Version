# ts_forecast.py
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import os

_hpi_series = None
_model_fit = None


def load_hpi_and_fit(csv_path='artifacts/bangalore_hpi.csv', arima_order=(1, 1, 1)):
    """
    Load HPI CSV (Quarter, ALL columns), parse to datetime, and fit ARIMA model.
    CSV must have columns: Quarter, ALL (or similar)
    """
    global _hpi_series, _model_fit

    base = os.path.dirname(__file__)
    path = os.path.join(base, csv_path) if not os.path.isabs(csv_path) else csv_path

    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ CSV not found at {path}")

    df = pd.read_csv(path)

    # Handle both "Quarter" and "Date" column names
    if 'Quarter' in df.columns:
        date_col = 'Quarter'
    elif 'Date' in df.columns:
        date_col = 'Date'
    else:
        raise KeyError("❌ CSV must contain a 'Quarter' or 'Date' column.")

    # Convert to datetime safely
    df[date_col] = pd.to_datetime(df[date_col], format='%b-%y', errors='coerce')
    df.dropna(subset=[date_col], inplace=True)
    df.sort_values(date_col, inplace=True)
    df.set_index(date_col, inplace=True)

    # Detect column to use for HPI
    if 'ALL' in df.columns:
        hpi_col = 'ALL'
    elif 'HPI' in df.columns:
        hpi_col = 'HPI'
    else:
        raise KeyError("❌ CSV must have an 'ALL' or 'HPI' column.")

    _hpi_series = df[hpi_col].astype(float)

    # Force quarterly frequency
    _hpi_series.index = pd.DatetimeIndex(_hpi_series.index).to_period('Q').to_timestamp('Q')

    # Fit ARIMA
    model = ARIMA(_hpi_series, order=arima_order)
    _model_fit = model.fit()

    print("✅ ARIMA model fitted successfully on HPI data.")
    return True


def forecast_hpi(steps=12):
    """Forecast next `steps` quarters using the fitted ARIMA model."""
    global _model_fit, _hpi_series
    if _model_fit is None:
        raise RuntimeError("ARIMA model not fitted. Call load_hpi_and_fit() first.")

    res = _model_fit.get_forecast(steps=steps)
    forecast = res.predicted_mean
    conf_int = res.conf_int()

    # Create forecast dates
    last_date = _hpi_series.index[-1]
    forecast_index = pd.date_range(start=last_date + pd.offsets.QuarterEnd(),
                                   periods=steps, freq='Q')
    forecast.index = forecast_index

    return forecast, conf_int


def get_market_forecast_summary(steps=12):
    """Returns (growth_rate, volatility, risk_label, forecast_series)"""
    global _hpi_series
    if _hpi_series is None:
        raise RuntimeError("HPI data not loaded. Call load_hpi_and_fit() first.")

    forecast, _ = forecast_hpi(steps=steps)
    last_hist = _hpi_series.iloc[-1]
    last_fore = forecast.iloc[-1]
    growth_rate = (last_fore - last_hist) / last_hist

    # Volatility based on historical returns
    returns = _hpi_series.pct_change().dropna()
    volatility = float(returns.std())

    # Simple risk classification
    if growth_rate > 0.05 and volatility < 0.02:
        risk = "Low"
    elif growth_rate > -0.02:
        risk = "Moderate"
    else:
        risk = "High"

    return float(growth_rate), float(volatility), risk, forecast


if __name__ == "__main__":
    load_hpi_and_fit()
    gr, vol, risk, f = get_market_forecast_summary(steps=8)
    print("📈 Growth rate:", gr)
    print("📊 Volatility:", vol)
    print("⚠️ Risk level:", risk)
    print(f.tail())
