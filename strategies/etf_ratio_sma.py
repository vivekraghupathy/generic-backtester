import pandas as pd
from core.strategy import BaseStrategy

class ETFRatioSMAStrategy(BaseStrategy):
    """
    ETF Rotation Strategy (Ratio-Based Moving Average)
    Rule: 
    - Ratio = NIFTYBEES / GOLDBEES
    - Switch to NIFTY: If Ratio > SMA(Ratio, 50) * (1 + buffer)
    - Switch to GOLD: If Ratio < SMA(Ratio, 50) * (1 - buffer)
    - Inside buffer: Maintain current position.
    """
    def __init__(self, name="RatioSMA", sma_period=50, buffer_pct=0.01):
        super().__init__(name)
        self.sma_period = sma_period
        self.buffer_pct = buffer_pct
        self.nifty_ticker = "NIFTYBEES.NS"
        self.gold_ticker = "GOLDBEES.NS"

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> Calculating Ratio SMA{self.sma_period} (Nifty/Gold)...")
        
        # 1. Align and calculate Ratio
        df_nifty = df[df['Ticker'] == self.nifty_ticker].copy()
        df_gold = df[df['Ticker'] == self.gold_ticker].copy()
        
        # Standardize index to Date for alignment
        nifty_close = df_nifty.set_index('Date')['Close']
        gold_close = df_gold.set_index('Date')['Close']
        
        # Ratio of Nifty to Gold
        ratio = nifty_close / gold_close
        ratio_sma = ratio.rolling(window=self.sma_period).mean()
        
        # 2. Map back to main DF
        df['NIFTY_GOLD_Ratio'] = df['Date'].map(ratio)
        df['Ratio_SMA'] = df['Date'].map(ratio_sma)
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        if day_data.empty:
            return pd.DataFrame(columns=day_data.columns)
            
        row = day_data.iloc[0]
        if pd.isna(row['Ratio_SMA']):
            return pd.DataFrame(columns=day_data.columns)
            
        ratio = row['NIFTY_GOLD_Ratio']
        sma = row['Ratio_SMA']
        
        if ratio > sma * (1 + self.buffer_pct):
            target_ticker = self.nifty_ticker
        elif ratio < sma * (1 - self.buffer_pct):
            target_ticker = self.gold_ticker
        else:
            # Maintain current position
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
        ratio = row['NIFTY_GOLD_Ratio']
        sma = row['Ratio_SMA']
        is_nifty = row['Ticker'] == self.nifty_ticker
        
        if is_nifty:
            # Exit Nifty if Ratio breaks below lower buffer
            if ratio < sma * (1 - self.buffer_pct):
                return True, row['Open'], "Ratio Cross Down"
        else:
            # Exit Gold if Ratio breaks above upper buffer
            if ratio > sma * (1 + self.buffer_pct):
                return True, row['Open'], "Ratio Cross Up"
                
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "sma_period": self.sma_period,
            "buffer_pct": self.buffer_pct,
            "nifty_ticker": self.nifty_ticker,
            "gold_ticker": self.gold_ticker
        }
