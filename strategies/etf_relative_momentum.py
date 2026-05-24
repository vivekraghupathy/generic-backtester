import pandas as pd
from core.strategy import BaseStrategy

class ETRelativeMomentumStrategy(BaseStrategy):
    """
    Relative Momentum Strategy (NIFTYBEES vs GOLDBEES)
    Rule: 
    - Hold the asset with the higher Rate of Change (ROC) over the lookback period.
    - Uses a small relative buffer to avoid whipsaws.
    """
    def __init__(self, name="RelativeMomentum", lookback=60, buffer_pct=0.005):
        super().__init__(name)
        self.lookback = lookback
        self.buffer_pct = buffer_pct
        self.nifty_ticker = "NIFTYBEES.NS"
        self.gold_ticker = "GOLDBEES.NS"

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> Calculating {self.lookback}-day ROC for cross-sectional comparison...")
        
        # Calculate ROC for each ticker independently
        groups = df.groupby('Ticker')
        df['ROC'] = groups['Close'].transform(lambda x: x.pct_change(periods=self.lookback))
        
        # Cross-map ROCs so each row knows both assets' momentum
        df_nifty = df[df['Ticker'] == self.nifty_ticker].copy()
        df_gold = df[df['Ticker'] == self.gold_ticker].copy()
        
        nifty_roc_map = df_nifty.set_index('Date')['ROC']
        gold_roc_map = df_gold.set_index('Date')['ROC']
        
        df['NIFTY_ROC'] = df['Date'].map(nifty_roc_map)
        df['GOLD_ROC'] = df['Date'].map(gold_roc_map)
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        if day_data.empty:
            return pd.DataFrame(columns=day_data.columns)
            
        row = day_data.iloc[0]
        if pd.isna(row['NIFTY_ROC']) or pd.isna(row['GOLD_ROC']):
            return pd.DataFrame(columns=day_data.columns)
            
        nifty_roc = row['NIFTY_ROC']
        gold_roc = row['GOLD_ROC']
        
        # Logic with Buffer: To switch, the other asset must be significantly stronger
        # Since we rotate between just two, we signal the target.
        if nifty_roc > gold_roc + self.buffer_pct:
            target_ticker = self.nifty_ticker
        elif gold_roc > nifty_roc + self.buffer_pct:
            target_ticker = self.gold_ticker
        else:
            # Inside buffer zone, maintain current (signal empty)
            return pd.DataFrame(columns=day_data.columns)
            
        return day_data[day_data['Ticker'] == target_ticker]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        entry_price = row['Open']
        shares = cash // entry_price
        return {
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': 0
        }

    def check_exit(self, row: pd.Series, position: dict) -> tuple:
        nifty_roc = row['NIFTY_ROC']
        gold_roc = row['GOLD_ROC']
        is_nifty = row['Ticker'] == self.nifty_ticker
        
        if is_nifty:
            # Exit NIFTY only if GOLD momentum is definitively stronger
            if gold_roc > nifty_roc + self.buffer_pct:
                return True, row['Open'], "Rotation to Gold"
        else:
            # Exit GOLD only if NIFTY momentum is definitively stronger
            if nifty_roc > gold_roc + self.buffer_pct:
                return True, row['Open'], "Rotation to Nifty"
                
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "lookback": self.lookback,
            "buffer_pct": self.buffer_pct,
            "nifty_ticker": self.nifty_ticker,
            "gold_ticker": self.gold_ticker
        }
