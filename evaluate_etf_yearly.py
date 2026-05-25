import os
import pandas as pd
from core.engine import BacktestEngine
from strategies.etf_rotation import ETFRotationStrategy
from strategies.etf_relative_momentum import ETRelativeMomentumStrategy
from strategies.etf_ratio_sma import ETFRatioSMAStrategy
from strategies.etf_dual_momentum import ETFDualMomentumStrategy

def main():
    DATA_FILE = 'data/etf_10y_data.parquet'
    INITIAL_CAPITAL = 1000000
    
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file {DATA_FILE} not found.")
        return

    # Load full dataset once to get year range
    full_df = pd.read_parquet(DATA_FILE)
    full_df['Date'] = pd.to_datetime(full_df['Date'])
    years = sorted(full_df['Date'].dt.year.unique())
    
    yearly_results = []

    print(f"Starting Yearly Backtest for {years[0]} to {years[-1]} (Dual Momentum 30D)...")
    print("-" * 60)
    print(f"{'Year':<6} | {'Return':<10} | {'Trades':<8} | {'Win Rate':<8} | {'Final Equity':<12}")
    print("-" * 60)

    for year in years:
        # Filter data for this year
        year_start = pd.Timestamp(year, 1, 1)
        year_end = pd.Timestamp(year, 12, 31)
        
        # Dual Momentum Strategy (30 days)
        strategy = ETFDualMomentumStrategy(lookback=30, buffer_pct=0.005)
        
        # Save temp file for this year (with buffer for indicators)
        start_with_buffer = year_start - pd.Timedelta(days=150)
        df_year = full_df[(full_df['Date'] >= start_with_buffer) & (full_df['Date'] <= year_end)]
        
        TEMP_FILE = f'data/temp_year_{year}.parquet'
        df_year.to_parquet(TEMP_FILE, index=False)
        
        engine = BacktestEngine(
            data_file=TEMP_FILE,
            strategy=strategy,
            initial_capital=INITIAL_CAPITAL,
            max_positions=1,
            summary_file=f'results_yearly_{year}.csv',
            commission_pct=0.001,
            tax_rates={
                "NIFTYBEES.NS": 0.20, # 20% STCG
                "GOLDBEES.NS": 0.30   # 30% Gold Tax
            }
        )
        
        # Monkey patch engine to only record trades/equity curve WITHIN the year
        # Actually, let's just run it and filter the trades DF later
        engine.run()
        
        # Results analysis for this year
        # We need to filter trades that ended in this year
        if os.path.exists('trades.csv'):
            trades_df = pd.read_csv('trades.csv')
            trades_df['ExitDate'] = pd.to_datetime(trades_df['ExitDate'])
            year_trades = trades_df[trades_df['ExitDate'].dt.year == year]
            
            equity_df = pd.read_csv('equity.csv')
            equity_df['Date'] = pd.to_datetime(equity_df['Date'])
            year_equity = equity_df[equity_df['Date'].dt.year == year]
            
            if not year_equity.empty:
                start_eq = year_equity.iloc[0]['Equity']
                end_eq = year_equity.iloc[-1]['Equity']
                ret = (end_eq / start_eq) - 1
                trades_count = len(year_trades)
                win_rate = (year_trades['Gain'] > 0).mean() if trades_count > 0 else 0
                
                print(f"{year:<6} | {ret:>9.2%} | {trades_count:<8} | {win_rate:>7.1%} | {end_eq:>12,.0f}")
                
                yearly_results.append({
                    'Year': year,
                    'Return': ret,
                    'Trades': trades_count,
                    'WinRate': win_rate,
                    'FinalEquity': end_eq
                })
        
        # Cleanup temp files
        if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
        for f in [f'results_yearly_{year}.csv']:
            if os.path.exists(f): os.remove(f)

    print("-" * 60)
    total_ret_overall = pd.DataFrame(yearly_results)['Return'].add(1).prod() - 1
    print(f"Compounded 10Y Return: {total_ret_overall:.2%}")

if __name__ == "__main__":
    main()
