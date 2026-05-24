import pandas as pd
from core.strategy import BaseStrategy

class GapUpMomentumStrategy(BaseStrategy):
    """
    9:20 AM Gap Up Strategy (Daily Adaptation)
    Target: Stocks gapping up > 2% in a medium-term uptrend.
    Exit: 5-day EMA trailing stop or 5% hard stop.
    """
    def __init__(self, name="GapUpMomentum", gap_pct=0.02, roc_period=20, ema_period=5, stop_loss_pct=0.05, volume_surge=None):
        super().__init__(name)
        self.gap_pct = gap_pct
        self.roc_period = roc_period
        self.ema_period = ema_period
        self.stop_loss_pct = stop_loss_pct
        self.volume_surge = volume_surge

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> EMA{self.ema_period}, ROC{self.roc_period}, VolEMA21...")
        groups = df.groupby('Ticker')
        
        # EMA for trailing exit
        df['EMA_Exit'] = groups['Close'].transform(lambda x: x.ewm(span=self.ema_period, adjust=False).mean())
        
        # ROC for trend filter
        df['ROC_Filter'] = groups['Close'].transform(lambda x: x.pct_change(periods=self.roc_period))
        
        # Volume EMA for volume surge filter
        df['VolEMA21'] = groups['Volume'].transform(lambda x: x.ewm(span=21, adjust=False).mean())

        # Shift close to calculate gap
        df['PrevClose'] = groups['Close'].shift(1)
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        # Filter for Gap Up and Positive momentum
        gap_up = (day_data['Open'] / day_data['PrevClose']) - 1 > self.gap_pct
        trend_filter = day_data['ROC_Filter'] > 0
        
        trigger = gap_up & trend_filter

        # Optional Volume Surge Filter
        if self.volume_surge:
            trigger = trigger & (day_data['Volume'] > self.volume_surge * day_data['VolEMA21'])
        
        return day_data[trigger]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        # Buy at Open + 0.5% buffer to simulate catching the opening range break
        entry_price = row['Open'] * 1.005
        
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
        
        # 2. EMA Trailing Stop (Close below EMA)
        if row['Close'] < row['EMA_Exit']:
            return True, row['Close'], f"EMA{self.ema_period} Cross"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "gap_pct": self.gap_pct,
            "roc_period": self.roc_period,
            "ema_period": self.ema_period,
            "stop_loss_pct": self.stop_loss_pct,
            "volume_surge": self.volume_surge,
            "slippage_buffer": 0.005
        }
