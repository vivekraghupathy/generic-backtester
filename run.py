import os
import pandas as pd
from core.engine import BacktestEngine
from strategies.episodic_pivot import EpisodicPivotStrategy
from strategies.gap_up_momentum import GapUpMomentumStrategy
from strategies.power_dip import PowerDipStrategy

def main():
    # Configuration - Load both files to get enough history for SMA200
    FILE_1 = 'data/nifty500_ohlcv_2024_2025.parquet'
    FILE_2 = 'data/nifty500_ohlcv_2025_2026.parquet'
    INITIAL_CAPITAL = 1000000
    MAX_POSITIONS = 10
    
    if not os.path.exists(FILE_1) or not os.path.exists(FILE_2):
        print(f"Error: Data files not found.")
        return

    print("Loading and concatenating datasets for multi-year history...")
    df1 = pd.read_parquet(FILE_1)
    df2 = pd.read_parquet(FILE_2)
    # Join and drop duplicates (April 2025 likely overlaps)
    full_df = pd.concat([df1, df2]).drop_duplicates(subset=['Ticker', 'Date']).sort_values(['Ticker', 'Date'])
    
    # Save temporary full dataset for the engine
    DATA_FILE = 'data/nifty500_full_history.parquet'
    full_df.to_parquet(DATA_FILE, index=False)

    # Initialize Strategy
    from strategies.fifty_two_week_high import FiftyTwoWeekHighStrategy
    strategy = FiftyTwoWeekHighStrategy()

    # Initialize Engine
    engine = BacktestEngine(
        data_file=DATA_FILE,
        strategy=strategy,
        initial_capital=INITIAL_CAPITAL,
        max_positions=MAX_POSITIONS
    )

    # Run Backtest
    engine.run()

if __name__ == "__main__":
    main()
