# Strategy Backtesting Framework

A modular options and futures backtesting engine for the stock market (NIFTY and BANKNIFTY). This framework processes tick-level data (down-sampled to 1-second intervals), executes an automated Rolling Straddle options strategy, and generates comprehensive performance metrics and plots for analysis.

## Features

* **Tick-Level Processing Engine:** Uses 1-second forward-filled timelines for accurate tick-by-tick simulation.
* **Pluggable Base Strategy:** Built to be strategy-agnostic; the `Strategy` base class allows seamless integration of new trading algorithms without changing the core engine.
* **Rolling Straddle Implementation:** Includes a pre-configured `RollingStraddleStrategy` that maintains a constant  CE (Call) + PE (Put) hold by rolling positions dynamically as the underlying Futures price moves.
* **Automated MTM & Portfolio Tracking:** Simulates entry/exit fills, handles live Mark-to-Market (MTM) calculations, closes open positions at Session End, and keeps a complete trade log.
* **Extensive Visual Analytics:** Generates daily PnL charts, drawdown charts, cumulative NIFTY vs BANKNIFTY PnL, 15-minute intraday heatmaps, strike roll intensity heatmaps, and worst-day case study visualizers.

## Codebase Architecture

* `run_backtest.py`: The entry point script where the strategy, backtest engine, and results analyzer are orchestrated.
* `backtest_engine.py`: Controls the market timeline simulation (9:15 AM to 3:30 PM), manages tick data, and triggers strategy condition checks.
* `strategy.py`: Holds trading logic. Derive from the `Strategy` class here to implement your own indicators and entry/exit patterns.
* `data_utils.py`: Utilities for directory traversal, string parsing (Instrument names into Strike, Option type, Expiry), and Pandas data ingestion.
* `orders.py`: Definitions for simple transaction models (Buy/Sell, entry price and timestamps).
* `portfolio.py`: The portfolio container holding Realized/Unrealized PnL, execution history, and active holds.
* `results_analyzer.py`: A visualization and data reporting class that consumes portfolio statistics to yield graphs inside the `plots/` directory.

The codebase also contains the report which details all the findings obtained from the data.

## Getting Started

### Data Requirements
This repository relies on historical tick data organized precisely as follows:
```text
allData/
├── NSE_20221101/
│   ├── Futures (Continuous)/
│   │   ├── NIFTY-I.csv
│   │   └── BANKNIFTY-I.csv
│   └── Options/
│       ├── NIFTY22110318000CE.csv
│       ├── BANKNIFTY22110341000PE.csv
│       └── ...
└── NSE_20221102/
    ├── Futures (Continuous)/
    └── Options/
```
Ensure your extracted dataset is placed at the root of the project or rename your dataset as "allData" .

### Running the Backtest
Simply execute the main orchestration script. Ensure you have `pandas`, `numpy`, and `matplotlib` installed.

```bash
pip install pandas numpy matplotlib
python run_backtest.py
```
This will run the straddle simulation over all dates available in the `allData` directory, save the summary to a `results.txt` file, and produce charts.

## Results & Output
After the backtest completes, performance records will be neatly formatted and saved to `results.txt` in the root folder:
```text
========================================
          BACKTEST SUMMARY              
========================================
Final total PnL:             XXXX.XX
Final realized PnL:          XXXX.XX
Total trades closed:             YYY
Win rate:                       ZZ.Z%
Average PnL / trade:         XXXX.XX
========================================
```

A `plots/` folder will be generated showcasing:
* `cumulative_pnl.png` — Visual breakdown of realized vs unrealized PnL over time.
* `daily_pnl.png` — Daily bar graphs tracing profit/loss day-by-day.
* `drawdown.png` — Peak-to-trough drop measuring model risk.
* `intraday_pnl_heatmap.png` — Highlights highly profitable/unprofitable times of day.
* `strike_roll_heatmap.png` — Displays periods of max volatility based on straddle rolling frequency.
* `trades_per_day.png`, `daily_pnl_vs_rolls.png` — Strike-roll related charts.

## How to Update

* **Trading different Instruments/Underliers:** 
  Modify the `UNDERLIERS_TO_TRADE` list inside `run_backtest.py`.
* **Testing new logic and Strategies:** 
  In `strategy.py`, create a new class inheriting from `Strategy`. You must implement the `on_tick(...)` function to return valid `Order` entries based on market status. Then, construct and pass your custom class instance inside `run_backtest.py`.
* **Modifying Duration Constraints:** 
  The backtest runs from 09:15:00 to 15:30:00 every day on a 1-second frequency. You can modify these defaults inside `backtest_engine.py` (`SESSION_START_TIME`, `SESSION_END_TIME`, `TICK_FREQUENCY`).
