import pandas as pd
from core.strategy import BaseStrategy

class ETFRotationStrategy(BaseStrategy):
    """
    ETF Rotation Strategy (NIFTYBEES vs GOLDBEES)
    Rule: 
    - If NIFTYBEES > SMA50 * (1 + buffer): 100% in NIFTYBEES
    - If NIFTYBEES < SMA50 * (1 - buffer): 100% in GOLDBEES
    - Inside buffer: Maintain current position.
    """
    def __init__(self, name="ETFRotation", sma_period=50, buffer_pct=0.01):
        super().__init__(name)
        self.sma_period = sma_period
        self.buffer_pct = buffer_pct
        self.nifty_ticker = "NIFTYBEES.NS"
        self.gold_ticker = "GOLDBEES.NS"

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f" -> Calculating SMA{self.sma_period} for {self.nifty_ticker}...")
        
        # Create a helper for NIFTY SMA
        df_nifty = df[df['Ticker'] == self.nifty_ticker].copy()
        df_nifty['NIFTY_SMA'] = df_nifty['Close'].rolling(window=self.sma_period).mean()
        
        # Map SMA back to the main dataframe for all rows of the same date
        sma_map = df_nifty.set_index('Date')['NIFTY_SMA']
        df['NIFTY_SMA'] = df['Date'].map(sma_map)
        
        # Also get NIFTY's close price to compare with SMA on every date
        nifty_close_map = df_nifty.set_index('Date')['Close']
        df['NIFTY_Close'] = df['Date'].map(nifty_close_map)
        
        return df

    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        if day_data.empty:
            return pd.DataFrame(columns=day_data.columns)
            
        nifty_row = day_data[day_data['Ticker'] == self.nifty_ticker]
        if nifty_row.empty or pd.isna(nifty_row.iloc[0]['NIFTY_SMA']):
            return pd.DataFrame(columns=day_data.columns) # Wait for indicators
            
        close = nifty_row.iloc[0]['NIFTY_Close']
        sma = nifty_row.iloc[0]['NIFTY_SMA']
        
        if close > sma * (1 + self.buffer_pct):
            target_ticker = self.nifty_ticker
        elif close < sma * (1 - self.buffer_pct):
            target_ticker = self.gold_ticker
        else:
            # Inside the "no-trade" buffer zone
            return pd.DataFrame(columns=day_data.columns)
        
        return day_data[day_data['Ticker'] == target_ticker]

    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        # Enter at Open
        entry_price = row['Open']
        
        # 100% Allocation
        shares = cash // entry_price
        
        return {
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': 0 # No hard stop for rotation
        }

    def check_exit(self, row: pd.Series, position: dict) -> tuple:
        # Exit logic: if the current ticker is definitively invalid
        close = row['NIFTY_Close']
        sma = row['NIFTY_SMA']
        is_nifty = row['Ticker'] == self.nifty_ticker
        
        if is_nifty:
            # Exit NIFTY only if it breaks below the LOWER buffer
            if close < sma * (1 - self.buffer_pct):
                return True, row['Open'], "Exit Nifty (Below Buffer)"
        else:
            # Exit GOLD only if NIFTY breaks above the UPPER buffer
            if close > sma * (1 + self.buffer_pct):
                return True, row['Open'], "Exit Gold (Above Buffer)"
            
        return False, 0, ""

    def get_params(self) -> dict:
        return {
            "sma_period": self.sma_period,
            "buffer_pct": self.buffer_pct,
            "nifty_ticker": self.nifty_ticker,
            "gold_ticker": self.gold_ticker
        }
