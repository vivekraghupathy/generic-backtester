import pandas as pd
import numpy as np
from core.strategy import BaseStrategy

class VCPBreakoutStrategy(BaseStrategy):
    """
    Minervini-style VCP Breakout Strategy
    Target: Stocks in a trend (ROC60 > 0) breaking out after volatility contraction.
    Exit: EMA21 Cross or 8% hard stop.
    """
    def __init__(self, name="VCPBreakout", sma_fast=50, sma_slow=200, vol_ratio=0.65, volume_surge=2.0, stop_loss_pct=0.08, ema_exit=21):
        super().__init__(name)
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow
        self.vol_ratio = vol_ratio
        self.volume_surge = volume_surge
        self.stop_loss_pct = stop_loss_pct
        self.ema_exit = ema_exit

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> Stage 2 (SMA{self.sma_fast}/{self.sma_slow}), Squeeze, Proximity, EMA{self.ema_exit}...")
        groups = df.groupby('Ticker')
        
        # 1. Stage 2 Trend Filter
        df['SMA50'] = groups['Close'].transform(lambda x: x.rolling(window=self.sma_fast).mean())
        df['SMA200'] = groups['Close'].transform(lambda x: x.rolling(window=self.sma_slow).mean())
        
        # 2. Volatility Contraction (StdDev 10 vs 50)
        df['Std10'] = groups['Close'].transform(lambda x: x.rolling(window=10).std())
        df['Std50'] = groups['Close'].transform(lambda x: x.rolling(window=50).std())
        df['Vol_Ratio'] = df['Std10'] / df['Std50']
        
        # 3. Proximity to 52-week High
        df['High52'] = groups['High'].transform(lambda x: x.rolling(window=252).max())
        df['Dist_From_High'] = (df['High52'] - df['Close']) / df['High52']

        # 4. Breakout Level (20-day high)
        df['PrevHigh20'] = groups['High'].transform(lambda x: x.shift(1).rolling(window=20).max())
        
        # 5. Volume Filter
        df['VolEMA21'] = groups['Volume'].transform(lambda x: x.ewm(span=21, adjust=False).mean())
        
        # 6. Exit Indicator
        df['Exit_EMA'] = groups['Close'].transform(lambda x: x.ewm(span=self.ema_exit, adjust=False).mean())
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        # Rules (Classic Minervini + VCP):
        # 1. Trend: Price > SMA50 AND SMA50 > SMA200 (Stage 2)
        # 2. Breakout: Current High > Prev 20-day High
        # 3. Contraction: Vol_Ratio < 0.65
        # 4. Proximity: Within 10% of 52-week High
        # 5. Volume: Vol > 2.0x average
        
        stage2 = (day_data['Close'] > day_data['SMA50']) & (day_data['SMA50'] > day_data['SMA200'])
        breakout = day_data['High'] > day_data['PrevHigh20']
        squeeze = day_data['Vol_Ratio'] < self.vol_ratio
        proximity = day_data['Dist_From_High'] < 0.10
        volume = day_data['Volume'] > (self.volume_surge * day_data['VolEMA21'])
        
        return day_data[stage2 & breakout & squeeze & proximity & volume]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        # Buy at the Breakout Level
        entry_price = max(row['Open'], row['PrevHigh20'] * 1.001)
        
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
        
        # 2. Trend Exit (Close below EMA)
        if row['Close'] < row['Exit_EMA']:
            return True, row['Close'], f"EMA{self.ema_exit} Cross"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "sma_fast": self.sma_fast,
            "sma_slow": self.sma_slow,
            "vol_ratio": self.vol_ratio,
            "volume_surge": self.volume_surge,
            "proximity_to_high": 0.10,
            "stop_loss_pct": self.stop_loss_pct,
            "ema_exit": self.ema_exit
        }
