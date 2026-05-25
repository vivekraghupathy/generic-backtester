import pandas as pd
from core.strategy import BaseStrategy

class Nifty500RelativeMomentum(BaseStrategy):
    """
    Relative Momentum for Nifty 500
    Rule: 
    1. Calculate X-day ROC for all stocks.
    2. Rank all stocks by ROC.
    3. Buy the Top N stocks.
    4. Rebalance periodically or when a stock falls out of Top N + Buffer.
    """
    def __init__(self, name="Nifty500RelMom", lookback=90, top_n=20, rank_buffer=10):
        super().__init__(name)
        self.lookback = lookback
        self.top_n = top_n
        self.rank_buffer = rank_buffer # Stay in top_n + rank_buffer to avoid churn

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> Calculating {self.lookback}-day ROC for Nifty 500 stocks...")
        groups = df.groupby('Ticker')
        df['ROC'] = groups['Close'].transform(lambda x: x.pct_change(periods=self.lookback))
        
        # We need to rank stocks cross-sectionally for every date
        print(" -> Ranking stocks cross-sectionally by date...")
        df['Rank'] = df.groupby('Date')['ROC'].rank(ascending=False, method='first')
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        # Buy stocks ranked in the top_n
        signals = day_data[day_data['Rank'] <= self.top_n]
        return signals

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        entry_price = row['Open']
        
        # Allocation logic: distribute remaining cash equally among available slots
        available_slots = total_max_positions - current_position_count
        if available_slots <= 0:
            return {'shares': 0, 'entry_price': entry_price, 'stop_loss': 0}
            
        allocation = cash / available_slots
        shares = allocation // entry_price
        
        return {
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': 0 # Momentum exit only
        }

    def check_exit(self, row: pd.Series, position: dict) -> tuple:
        # Exit if the rank falls below top_n + rank_buffer
        current_rank = row['Rank']
        
        if pd.isna(current_rank) or current_rank > (self.top_n + self.rank_buffer):
            return True, row['Open'], f"Rank {current_rank} out of Top {self.top_n + self.rank_buffer}"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "lookback": self.lookback,
            "top_n": self.top_n,
            "rank_buffer": self.rank_buffer
        }
