import pandas as pd
import numpy as np
from core.strategy import BaseStrategy

class PowerDipStrategy(BaseStrategy):
    """
    Power Dip Strategy (Mean Reversion)
    Target: Stocks in a medium-term uptrend (ROC30 > 0) that have a sharp sell-off (RSI2 < 15).
    Exit: RSI2 > 70 or 8% hard stop.
    """
    def __init__(self, name="PowerDip", sma_period=50, rsi_period=2, entry_rsi=10, exit_rsi=70, stop_loss_pct=0.08):
        super().__init__(name)
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.entry_rsi = entry_rsi
        self.exit_rsi = exit_rsi
        self.stop_loss_pct = stop_loss_pct

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> SMA{self.sma_period}, RSI{self.rsi_period}...")
        groups = df.groupby('Ticker')
        
        # 1. SMA Trend Filter
        df['SMA_Trend'] = groups['Close'].transform(lambda x: x.rolling(window=self.sma_period).mean())
        
        # 2. RSI(2) Calculation
        def calculate_rsi(series, period):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df['RSI2'] = groups['Close'].transform(lambda x: calculate_rsi(x, self.rsi_period))
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        # Filter: Price > SMA50 (Uptrend) and RSI2 < 10 (Oversold Dip)
        trend_filter = day_data['Close'] > day_data['SMA_Trend']
        dip_filter = day_data['RSI2'] < self.entry_rsi
        
        valid = day_data['RSI2'].notna() & day_data['SMA_Trend'].notna()
        
        return day_data[trend_filter & dip_filter & valid]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        # Buy at the market open of the NEXT day
        # In our engine loop, 'row' is the day the signal was generated.
        # However, the engine enters on the SAME day the signal is provided in 'generate_signals'.
        # To simulate "Buy at Open of Day T+1", we will rely on the engine's next loop, 
        # but the current engine structure enters on the signal day.
        
        # FIX: For Mean Reversion, we usually buy the NEXT day's open.
        # In this engine, we will assume entry at 'row['Open']' of the current date 
        # (effectively signal was yesterday close).
        
        entry_price = row['Open']
        
        # Equal weighting
        risk_capital = cash / (total_max_positions - current_position_count)
        shares = risk_capital // entry_price
        
        return {
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': entry_price * (1 - self.stop_loss_pct)
        }

    def check_exit(self, row: pd.Series, position: dict) -> tuple:
        # 1. Hard Stop Loss
        if row['Low'] <= position['stop_loss']:
            return True, position['stop_loss'], "Hard Stop"
        
        # 2. RSI(2) Exit (Snapback)
        if row['RSI2'] > self.exit_rsi:
            return True, row['Close'], f"RSI{self.rsi_period} Exit"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "sma_period": self.sma_period,
            "rsi_period": self.rsi_period,
            "entry_rsi": self.entry_rsi,
            "exit_rsi": self.exit_rsi,
            "stop_loss_pct": self.stop_loss_pct
        }
