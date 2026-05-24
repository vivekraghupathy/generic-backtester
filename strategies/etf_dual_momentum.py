import pandas as pd
from core.strategy import BaseStrategy

class ETFDualMomentumStrategy(BaseStrategy):
    """
    Dual Momentum Strategy (Gary Antonacci Model)
    Rule:
    - Hold NIFTYBEES if: (NIFTY ROC > 0) AND (NIFTY ROC > GOLD ROC)
    - Else: Hold GOLDBEES
    """
    def __init__(self, name="DualMomentum", lookback=60, buffer_pct=0.005):
        super().__init__(name)
        self.lookback = lookback
        self.buffer_pct = buffer_pct
        self.nifty_ticker = "NIFTYBEES.NS"
        self.gold_ticker = "GOLDBEES.NS"

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> Calculating {self.lookback}-day ROC for Dual Momentum comparison...")
        
        # 1. Calculate ROC for each ticker
        groups = df.groupby('Ticker')
        df['ROC'] = groups['Close'].transform(lambda x: x.pct_change(periods=self.lookback))
        
        # 2. Cross-map ROCs
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
        
        # Dual Momentum Logic
        # 1. Absolute: Nifty > 0
        # 2. Relative: Nifty > Gold (with buffer)
        is_nifty_positive = nifty_roc > 0
        is_nifty_superior = nifty_roc > (gold_roc + self.buffer_pct)
        
        if is_nifty_positive and is_nifty_superior:
            target_ticker = self.nifty_ticker
        elif gold_roc > (nifty_roc + self.buffer_pct) or not is_nifty_positive:
            # If Gold is better, or Nifty is negative
            target_ticker = self.gold_ticker
        else:
            # Inside noise band, maintain position
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
        
        is_nifty_positive = nifty_roc > 0
        is_nifty_superior = nifty_roc > (gold_roc + self.buffer_pct)
        
        should_hold_nifty = is_nifty_positive and is_nifty_superior
        
        if is_nifty and not should_hold_nifty:
            return True, row['Open'], "Exit Nifty (Negative or Inferior Momentum)"
        elif not is_nifty and should_hold_nifty:
            return True, row['Open'], "Exit Gold (Nifty Superior)"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "lookback": self.lookback,
            "buffer_pct": self.buffer_pct,
            "nifty_ticker": self.nifty_ticker,
            "gold_ticker": self.gold_ticker
        }
