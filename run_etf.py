import os
import pandas as pd
from core.engine import BacktestEngine
from strategies.etf_rotation import ETFRotationStrategy

def main():
    DATA_FILE = 'data/etf_10y_data.parquet'
    INITIAL_CAPITAL = 1000000
    MAX_POSITIONS = 1 # 100% allocation strategy
    
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file {DATA_FILE} not found. Please run download_etf_data.py first.")
        return

    # Initialize Strategy
    strategy = ETFRotationStrategy(sma_period=50)

    # Initialize Engine
    engine = BacktestEngine(
        data_file=DATA_FILE,
        strategy=strategy,
        initial_capital=INITIAL_CAPITAL,
        max_positions=MAX_POSITIONS
    )

    # Filter data for specific period
    print("Filtering data for period: 2024-04-01 to 2026-04-30...")
    full_df = engine.load_data()
    filtered_df = full_df[(full_df['Date'] >= '2024-04-01') & (full_df['Date'] <= '2026-04-30')]
    
    # Override the run method's internal data loading by passing filtered_df if possible
    # Or just save to a temp file
    TEMP_DATA = 'data/etf_2y_filtered.parquet'
    filtered_df.to_parquet(TEMP_DATA, index=False)
    engine.data_file = TEMP_DATA

    # Run Backtest
    engine.run()

if __name__ == "__main__":
    main()
