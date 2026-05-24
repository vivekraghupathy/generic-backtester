import sys
import os

# Add the project root to sys.path so we can import from data_utils
sys.path.append(os.getcwd())

from data_utils.downloader import download_ohlcv_data
from datetime import datetime, timedelta

def main():
    symbols_file = 'data/ETF_DATA/etf_symbols.csv'
    output_file = 'data/etf_10y_data.parquet'
    
    # Calculate dates for 10 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*10)).strftime('%Y-%m-%d')
    
    print(f"Starting download for {start_date} to {end_date}...")
    download_ohlcv_data(symbols_file, output_file, start_date, end_date)

if __name__ == "__main__":
    main()
