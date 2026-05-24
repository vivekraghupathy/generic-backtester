import pandas as pd
import yfinance as yf
from datetime import datetime
import os
from tqdm import tqdm

def download_ohlcv_data(symbols_file, output_file, start_date, end_date):
    """
    Downloads OHLCV data for a list of symbols from yfinance and saves to Parquet.
    """
    print(f"Loading symbols from {symbols_file}...")
    if not os.path.exists(symbols_file):
        print(f"Error: {symbols_file} not found.")
        return
        
    symbols_df = pd.read_csv(symbols_file)
    ticker_col = 'Symbol' if 'Symbol' in symbols_df.columns else 'Ticker'
    symbols = symbols_df[ticker_col].tolist()
    
    all_data = []
    failed = []
    
    print(f"Downloading data from {start_date} to {end_date} for {len(symbols)} symbols...")
    
    for symbol in tqdm(symbols):
        try:
            ticker = f"{str(symbol).strip()}.NS"
            # auto_adjust=True handles splits/dividends
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if not df.empty:
                df = df.reset_index()
                # Flatten multi-index if it exists (yfinance v0.2.x behavior)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                
                df['Ticker'] = ticker
                # Ensure standard columns
                cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']
                df = df[cols]
                all_data.append(df)
            else:
                failed.append(ticker)
        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            failed.append(symbol)

    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        master_df['Date'] = pd.to_datetime(master_df['Date'])
        print(f"Saving to {output_file}...")
        master_df.to_parquet(output_file, index=False)
        print(f"Saved {len(master_df)} rows for {len(all_data)} symbols.")
    else:
        print("No data downloaded.")
        
    if failed:
        print(f"Failed symbols ({len(failed)}): {failed}")

if __name__ == "__main__":
    # Example usage:
    # download_ohlcv_data('symbols.csv', 'data.parquet', '2025-01-01', '2026-05-23')
    pass
