import pandas as pd
import numpy as np
import time
import os
import json
from datetime import datetime
from .strategy import BaseStrategy

class BacktestEngine:
    def __init__(self, data_file, strategy: BaseStrategy, initial_capital=1000000, max_positions=10, debug_tickers=None, summary_file='results_summary.csv'):
        self.data_file = data_file
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.debug_tickers = debug_tickers
        self.summary_file = summary_file

    def load_data(self):
        start_time = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading data from {self.data_file}...")
        df = pd.read_parquet(self.data_file)
        print(f"-> Loaded {len(df)} rows. (Took {time.time() - start_time:.2f}s)")
        
        if self.debug_tickers:
            print(f"-> DEBUG MODE: Limiting to first {self.debug_tickers} tickers...")
            unique_tickers = df['Ticker'].unique()[:self.debug_tickers]
            df = df[df['Ticker'].isin(unique_tickers)]
            print(f"-> New row count: {len(df)}")

        start_time = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dropping NaNs and sorting...")
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(['Ticker', 'Date'])
        print(f"-> Cleaned and sorted. (Took {time.time() - start_time:.2f}s)")
        return df

    def run(self):
        df = self.load_data()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Calculating indicators using {self.strategy.name}...")
        start_calc = time.time()
        df = self.strategy.calculate_indicators(df)
        print(f"-> Calculations complete. (Took {time.time() - start_calc:.2f}s)")
        
        all_dates = sorted(df['Date'].unique())
        grouped = df.groupby('Date')
        
        cash = self.initial_capital
        positions = {} 
        trades = []
        equity_curve = []
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting simulation for {len(all_dates)} days...")
        sim_start = time.time()
        
        for i, date in enumerate(all_dates):
            if i % 100 == 0:
                print(f" -> Progress: {i}/{len(all_dates)} days processed... ({len(positions)} open positions)")
                
            day_data = grouped.get_group(date)
            
            # 1. Manage Exits
            for ticker in list(positions.keys()):
                pos = positions[ticker]
                row_list = day_data[day_data['Ticker'] == ticker]
                if row_list.empty: 
                    continue
                row = row_list.iloc[0]
                
                exit_triggered, exit_price, reason = self.strategy.check_exit(row, pos)
                
                if exit_triggered:
                    proceeds = pos['shares'] * exit_price
                    cash += proceeds
                    trades.append({
                        'Ticker': ticker, 
                        'EntryDate': pos['entry_date'], 
                        'ExitDate': date,
                        'EntryPrice': pos['entry_price'], 
                        'ExitPrice': exit_price,
                        'Shares': pos['shares'], 
                        'Gain': (exit_price / pos['entry_price']) - 1,
                        'Reason': reason
                    })
                    del positions[ticker]
            
            # 2. Manage Entries
            if len(positions) < self.max_positions:
                entries = self.strategy.generate_signals(day_data)
                # Filter out tickers already in positions
                entries = entries[~entries['Ticker'].isin(positions.keys())]
                
                for _, row in entries.iterrows():
                    if len(positions) >= self.max_positions: 
                        break
                    
                    entry_info = self.strategy.calculate_entry_price(row, cash, self.max_positions, len(positions))
                    
                    shares = entry_info.get('shares', 0)
                    entry_price = entry_info.get('entry_price', 0)
                    
                    if shares > 0:
                        cash -= shares * entry_price
                        positions[row['Ticker']] = {
                            'shares': shares, 
                            'entry_price': entry_price,
                            'entry_date': date, 
                            'stop_loss': entry_info.get('stop_loss', 0),
                            'initial_stop': entry_info.get('stop_loss', 0)
                        }
            
            # 3. Equity Tracking
            daily_equity = cash
            for t, p in positions.items():
                r = day_data[day_data['Ticker'] == t]
                daily_equity += p['shares'] * (r.iloc[0]['Close'] if not r.empty else p['entry_price'])
            equity_curve.append({'Date': date, 'Equity': daily_equity})
            
        print(f"-> Simulation complete. (Took {time.time() - sim_start:.2f}s)")
        self.report(trades, equity_curve)

    def report(self, trades, equity_curve):
        if not trades:
            print("No trades executed.")
            return
            
        trades_df = pd.DataFrame(trades)
        equity_df = pd.DataFrame(equity_curve)
        
        print("\n" + "="*40)
        print(f"      PERFORMANCE REPORT: {self.strategy.name}")
        print("="*40)
        
        final_equity = equity_df.iloc[-1]['Equity']
        total_return = (final_equity / self.initial_capital) - 1
        equity_df['Peak'] = equity_df['Equity'].cummax()
        equity_df['Drawdown'] = (equity_df['Equity'] / equity_df['Peak']) - 1
        max_dd = equity_df['Drawdown'].min()
        
        print(f"Initial Capital:  {self.initial_capital:,.2f}")
        print(f"Final Equity:     {final_equity:,.2f}")
        print(f"Total Return:     {total_return:.2%}")
        print(f"Max Drawdown:     {max_dd:.2%}")
        print(f"Total Trades:     {len(trades_df)}")
        print(f"Win Rate:         {(trades_df['Gain'] > 0).mean():.2%}")
        print(f"Average Trade:    {trades_df['Gain'].mean():.2%}")
        
        trades_df.to_csv('trades.csv', index=False)
        equity_df.to_csv('equity.csv', index=False)
        print("\nResults saved to 'trades.csv' and 'equity.csv'.")
        self.log_results_to_summary(final_equity, total_return, max_dd, len(trades_df), (trades_df['Gain'] > 0).mean(), trades_df['Gain'].mean())

    def log_results_to_summary(self, final_equity, total_return, max_dd, total_trades, win_rate, avg_trade):
        summary_path = self.summary_file
        file_exists = os.path.isfile(summary_path)
        
        result_row = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Strategy': self.strategy.name,
            'Parameters': json.dumps(self.strategy.get_params()),
            'InitialCapital': self.initial_capital,
            'FinalEquity': round(final_equity, 2),
            'TotalReturn': f"{total_return:.2%}",
            'MaxDrawdown': f"{max_dd:.2%}",
            'TotalTrades': total_trades,
            'WinRate': f"{win_rate:.2%}",
            'AvgTrade': f"{avg_trade:.2%}"
        }
        
        df = pd.DataFrame([result_row])
        df.to_csv(summary_path, mode='a', index=False, header=not file_exists)
        print(f"Results appended to '{summary_path}'.")
