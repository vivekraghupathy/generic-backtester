import os
import pandas as pd
from core.engine import BacktestEngine
from strategies.nifty500_relative_momentum import Nifty500RelativeMomentum

def main():
    DATA_FILE = 'data/nifty500_full_history.parquet'
    INITIAL_CAPITAL = 1000000
    MAX_POSITIONS = 20 # Hold Top 20 stocks
    
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file {DATA_FILE} not found.")
        return

    # Initialize Strategy
    # Lookback 60 days, target top 20, rank buffer of 10
    strategy = Nifty500RelativeMomentum(lookback=60, top_n=MAX_POSITIONS, rank_buffer=10)

    # Initialize Engine
    # Commission 0.1% (per switch), Tax 20% (STCG)
    engine = BacktestEngine(
        data_file=DATA_FILE,
        strategy=strategy,
        initial_capital=INITIAL_CAPITAL,
        max_positions=MAX_POSITIONS,
        commission_pct=0.001,
        tax_rates={}, 
        default_tax_rate=0.20, # Apply 20% tax to all Nifty 500 stocks
        rebalance_frequency='daily' # Back to Daily Rebalancing
    )

    # Note: For Nifty 500, we'll use a flat 20% tax rate in the engine if possible, 
    # but the engine currently uses a per-ticker map. 
    # Let's modify the engine slightly to handle a default tax rate.
    
    print("Starting Nifty 500 Relative Momentum Backtest...")
    engine.run()

if __name__ == "__main__":
    main()
