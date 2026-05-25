import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_weekly_signal():
    # 1. Configuration
    NIFTY_TICKER = "NIFTYBEES.NS"
    GOLD_TICKER = "GOLDBEES.NS"
    LOOKBACK = 30
    BUFFER = 0.005 # 0.5% buffer to avoid whipsaws
    
    print("=" * 50)
    print(f" ETF DUAL MOMENTUM WEEKLY SIGNAL - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 50)
    
    # 2. Fetch Data (Get ~90 days to ensure enough for 30-day ROC)
    print(f"Fetching latest data for {NIFTY_TICKER} and {GOLD_TICKER}...")
    
    tickers = [NIFTY_TICKER, GOLD_TICKER]
    data = yf.download(tickers, period="3mo", progress=False)['Close']
    
    if data.empty:
        print("Error: Could not fetch data from Yahoo Finance.")
        return

    # 3. Calculate 30-Day ROC
    # Current Price (last valid row)
    current_prices = data.iloc[-1]
    
    # Price 30 trading days ago
    # Note: Using -22 as a proxy for 30 calendar days if using daily rows, 
    # but since it's exactly 30 trading days in our backtest:
    start_prices = data.iloc[-LOOKBACK]
    
    roc_nifty = (current_prices[NIFTY_TICKER] / start_prices[NIFTY_TICKER]) - 1
    roc_gold = (current_prices[GOLD_TICKER] / start_prices[GOLD_TICKER]) - 1
    
    # 4. Display Metrics
    print("-" * 50)
    print(f"{'Asset':<15} | {'Price':<10} | {'30D Return':<10}")
    print("-" * 50)
    print(f"{'NIFTYBEES':<15} | {current_prices[NIFTY_TICKER]:>10.2f} | {roc_nifty:>9.2%}")
    print(f"{'GOLDBEES':<15} | {current_prices[GOLD_TICKER]:>10.2f} | {roc_gold:>9.2%}")
    print("-" * 50)
    
    # 5. Dual Momentum Logic
    # Rule 1: Absolute (Nifty > 0)
    is_absolute_positive = roc_nifty > 0
    
    # Rule 2: Relative (Nifty > Gold + Buffer)
    is_relative_superior = roc_nifty > (roc_gold + BUFFER)
    
    print(f"Conditions Check:")
    print(f" - Absolute Momentum (Nifty > 0):      {'YES' if is_absolute_positive else 'NO'}")
    print(f" - Relative Momentum (Nifty > Gold):   {'YES' if is_relative_superior else 'NO'}")
    print("-" * 50)
    
    # 6. Recommendation
    if is_absolute_positive and is_relative_superior:
        recommendation = "★★★ ALLOCATE 100% TO NIFTYBEES ★★★"
        reason = "Nifty is in an uptrend and outperforming Gold."
    else:
        recommendation = "★★★ ALLOCATE 100% TO GOLDBEES ★★★"
        if not is_absolute_positive:
            reason = "Nifty 30-day momentum is Negative (Safe Haven Mode)."
        else:
            reason = "Gold is outperforming Equity (Rotation Mode)."
            
    print(f"RECOMMENDATION: {recommendation}")
    print(f"REASON: {reason}")
    print("=" * 50)

if __name__ == "__main__":
    get_weekly_signal()
