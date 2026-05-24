# Generic Backtester Framework

A modular, extensible backtesting engine for quantitative trading strategies.

## Features
- **OOP Architecture**: Easily add new strategies by inheriting from `BaseStrategy`.
- **Vectorized Indicators**: Fast indicator calculation using Pandas.
- **Realistic Execution**: Support for slippage, realistic entry timing, and dynamic exits.
- **Portfolio Management**: Handles capital allocation, max positions, and equity tracking.

## Project Structure
- `core/`: Contains the `BacktestEngine` and `BaseStrategy` definition.
- `strategies/`: Implementation of specific trading strategies (e.g., `EpisodicPivotStrategy`, `FiftyTwoWeekHighStrategy`).
- `data_utils/`: Utilities for downloading and managing OHLCV data.
- `run.py`: Entry point for executing a backtest.

## Usage

### 1. Define a Strategy
Create a new file in `strategies/` and inherit from `BaseStrategy`. Implement the following methods:
- `calculate_indicators(df)`
- `generate_signals(day_data)`
- `calculate_entry_price(row, cash, ...)`
- `check_exit(row, position)`

### 2. Run a Backtest
Modify `run.py` to use your new strategy:
```python
from core.engine import BacktestEngine
from strategies.your_strategy import YourStrategy

strategy = YourStrategy()
engine = BacktestEngine(data_file='path/to/data.parquet', strategy=strategy)
engine.run()
```

## Performance Parity
The current `EpisodicPivotStrategy` has been verified to match the performance of the original standalone script:
- Total Return: 53.66%
- Max Drawdown: -11.47%
- Win Rate: 41.83%
