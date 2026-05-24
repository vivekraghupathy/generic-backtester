from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, name="BaseStrategy"):
        self.name = name

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform vectorized indicator calculations on the entire dataset.
        Should return the modified DataFrame.
        """
        pass

    @abstractmethod
    def generate_signals(self, day_data: pd.DataFrame) -> pd.DataFrame:
        """
        Identify candidates that trigger an entry signal on a given day.
        Returns a subset of day_data.
        """
        pass

    @abstractmethod
    def calculate_entry_price(self, row: pd.Series, cash: float, total_max_positions: int, current_position_count: int) -> dict:
        """
        Calculates the entry price, number of shares, and initial stop loss.
        Returns a dictionary with 'shares', 'entry_price', and 'stop_loss'.
        """
        pass

    @abstractmethod
    def check_exit(self, row: pd.Series, position: dict) -> tuple:
        """
        Evaluates whether an open position should be closed based on the current day's data.
        Returns (exit_triggered: bool, exit_price: float, reason: str).
        """
        pass

    def get_params(self) -> dict:
        """
        Returns a dictionary of strategy parameters for logging.
        """
        return {}
