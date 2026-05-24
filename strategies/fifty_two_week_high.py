import pandas as pd
from core.strategy import BaseStrategy

class FiftyTwoWeekHighStrategy(BaseStrategy):
    """
    52-Week High Breakout Strategy
    Target: Stocks breaking above their 52-week high on strong volume.
    Filter: Stage 2 trend (Price > SMA200).
    Exit: 21-day EMA trailing stop or 8% hard stop.
    """
    def __init__(self, name="52WeekHigh", sma_period=200, volume_surge=1.5, stop_loss_pct=0.08, trailing_ema=21, close_proximity=0.01):
        super().__init__(name)
        self.sma_period = sma_period
        self.volume_surge = volume_surge
        self.stop_loss_pct = stop_loss_pct
        self.trailing_ema = trailing_ema
        self.close_proximity = close_proximity

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> SMA{self.sma_period}, 52-Week High, VolEMA21, EMA{self.trailing_ema}...")
        groups = df.groupby('Ticker')
        
        # 1. 52-Week High (Highest High of last 252 days, excluding current day)
        df['High52'] = groups['High'].transform(lambda x: x.shift(1).rolling(window=252).max())
        
        # 2. Trend Filter (SMA200)
        df['SMA200'] = groups['Close'].transform(lambda x: x.rolling(window=self.sma_period).mean())
        
        # 3. Volume EMA
        df['VolEMA21'] = groups['Volume'].transform(lambda x: x.ewm(span=21, adjust=False).mean())
        
        # 4. Exit EMA
        df['Exit_EMA'] = groups['Close'].transform(lambda x: x.ewm(span=self.trailing_ema, adjust=False).mean())
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        # Rules:
        # 1. Breakout: Current High > Previous 52-week High
        # 2. Volume: Volume > 1.5x average
        # 3. Strong Close: Close is within X% of the daily high
        
        breakout = day_data['High'] > day_data['High52']
        volume = day_data['Volume'] > (self.volume_surge * day_data['VolEMA21'])
        strong_close = (day_data['High'] - day_data['Close']) / day_data['High'] <= self.close_proximity
        
        # Also ensure we have enough history (no NaNs)
        valid = day_data['High52'].notna()
        
        return day_data[breakout & volume & strong_close & valid]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        # Buy at the Breakout Level or Open if it gapped above
        entry_price = max(row['Open'], row['High52'] + 0.05) # Small buffer above high
        
        # Slippage: Assume we get filled slightly higher (0.5%)
        entry_price *= 1.005
        
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
        
        # 2. Trend Exit (Close below EMA21)
        if row['Close'] < row['Exit_EMA']:
            return True, row['Close'], f"EMA{self.trailing_ema} Cross"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "sma_period": self.sma_period,
            "volume_surge": self.volume_surge,
            "stop_loss_pct": self.stop_loss_pct,
            "trailing_ema": self.trailing_ema,
            "close_proximity": self.close_proximity,
            "lookback": 252
        }
