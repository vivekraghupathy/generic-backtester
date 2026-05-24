# Gap Up Momentum Strategy Summary

This strategy targets high-conviction gap-ups in stocks that are already demonstrating medium-term upward momentum. It aims to capture the post-gap "continuation" move while using a trailing stop to protect profits during short-term volatility.

---

## 1. Strategy Core Concept
The strategy filters for stocks that gap up significantly (> 4%) on high relative volume (> 2.0x average). The 20-day ROC filter ensures we are buying into established strength, avoiding "dead cat bounces."

---

## 2. Execution Rules

### Universe
*   **Nifty 500** (NSE India).

### Entry Criteria (The Signal)
*   **Price Gap:** Today's Open must be at least **4%** higher than the previous day's Close.
*   **Volume Surge:** Today's Volume must be **> 2.0x** the 21-day Volume EMA.
*   **Momentum Filter:** **ROC20 > 0** (The stock's price is higher than it was 20 trading days ago).

### Execution (Entry)
*   **Timing:** Buy at the market open (simulated with a 0.5% slippage/buffer to account for opening range execution).
*   **Price Logic:** `Entry = Open * 1.005`.

### Exit Criteria (Risk Management)
*   **Hard Stop Loss:** **5%** below the actual entry price.
*   **Trailing Stop:** Close the position if the daily price **closes below the 10-day EMA (EMA10)**.
    *   *Note: Testing showed EMA10 provides a better balance for absolute returns compared to the tighter EMA5.*

---

## 3. Backtest Results (May 2026)

Verified across the Nifty 500 universe for the April 2025 – May 2026 period.

| Metric | Performance |
| :--- | :--- |
| **Total Return** | **+47.44%** |
| **Max Drawdown** | **-9.53%** |
| **Win Rate** | 45.26% |
| **Total Trades** | 137 |
| **Average Trade** | +2.81% |
| **Max Positions** | 10 (10% capital per trade) |

---

## 4. Key Insights
1.  **Volume is Critical:** Requiring 2.0x volume significantly increased the average trade profit by filtering out weak "liquidity gaps."
2.  **Gap Threshold:** Increasing the gap requirement from 2% to 4% was the single most effective optimization step, reducing noise and increasing win rate.
3.  **Optimal Momentum:** ROC20 was found to be superior to ROC30, as it identifies the trend early enough to capture the meat of the gap continuation.

---

## 5. Practical Daily Routine (Manual Execution)

Follow these steps to execute the Gap Up Momentum strategy in real-time:

### Step 1: Pre-Market / Morning Scan (9:15 AM - 9:25 AM)
*   **Scan Nifty 500** for stocks gapping up **> 4%**.
*   **Filter 1:** Ensure the stock is in a medium-term uptrend (**ROC20 > 0**).
*   **Filter 2:** Check if the pre-market volume is already significant (trending toward **> 2x average**).

### Step 2: The 9:30 AM Entry
*   Confirm the stock has not "faded" the gap (it should be trading near or above the Open price).
*   **Execution:** Enter the position near the current price. 
*   *Note: In our backtest, we assume a 0.5% slippage from the open, so try to get filled within the first 15 minutes.*

### Step 3: Set Risk Levels (Immediate)
*   Calculate your **5% Hard Stop** based on your actual fill price and place the order immediately.
*   Plot the **10-day EMA (EMA10)** on your chart.

### Step 4: Daily Maintenance (Post-Market)
*   **Trailing Stop:** At the end of every trading day, check the **Closing Price**.
*   If the stock **closes below the EMA10**, sell the position at the next day's open (or at the close if you are monitoring in real-time).
*   *Rule: "Close below EMA10 = Exit." Do not exit just because the price touched the line intraday.*
