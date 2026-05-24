import pandas as pd
from core.strategy import BaseStrategy

class EpisodicPivotStrategy(BaseStrategy):
    def __init__(self, name="EpisodicPivot"):
        super().__init__(name)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(" -> EMA10/21, VolEMA21, ROC30...")
        groups = df.groupby('Ticker')
        df['EMA10'] = groups['Close'].transform(lambda x: x.ewm(span=10, adjust=False).mean())
        df['EMA21'] = groups['Close'].transform(lambda x: x.ewm(span=21, adjust=False).mean())
        df['VolEMA21'] = groups['Volume'].transform(lambda x: x.ewm(span=21, adjust=False).mean())
        df['ROC30'] = groups['Close'].transform(lambda x: x.pct_change(periods=30))
        
        print(" -> Shifting values...")
        df['PrevClose'] = groups['Close'].shift(1)
        df['PrevHigh'] = groups['High'].shift(1)
        
        print(" -> PctChange...")
        df['PctChange'] = (df['Close'] / df['PrevClose']) - 1
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        is_ep = (day_data['PctChange'] > 0.06) & (day_data['Volume'] > 2 * day_data['VolEMA21'])
        trigger = is_ep & (day_data['ROC30'] > 0)
        return day_data[trigger]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        # Realistic 9:30 AM Entry: Buy at Open/Breakout + 3% slippage
        base_entry = max(row['Open'], row['PrevHigh'] + 0.01)
        entry_price = base_entry * 1.03
        
        # Simple equal weighting
        risk_capital = cash / (total_max_positions - current_position_count)
        shares = risk_capital // entry_price
        
        return {
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': entry_price * 0.92
        }

    def check_exit(self, row: pd.Series, position: dict) -> tuple:
        if row['Low'] <= position['stop_loss']:
            return True, position['stop_loss'], "Stop Loss"
        elif row['Close'] < row['EMA21']:
            return True, row['Close'], "EMA21 Cross"
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "pct_thrust": 0.06,
            "vol_surge": 2.0,
            "roc_period": 30,
            "trailing_ema": 21,
            "stop_loss_pct": 0.08,
            "slippage_pct": 0.03
        }
