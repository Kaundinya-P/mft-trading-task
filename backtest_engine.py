import os
import pandas as pd

from data_utils import (
    get_trading_dates,
    build_options_index_for_date,
    load_futures_for_date,
    get_nearest_expiry,
    load_csv,
)
from portfolio import PortfolioTracker

SESSION_START_TIME = "09:15:00"
SESSION_END_TIME = "15:30:00"
TICK_FREQUENCY = "1s"


class BacktestEngine:
    """
    Runs the backtest day by day. For each day:
      1. Load futures and options data.
      2. Build a clean 1-second timeline for the session.
      3. Forward-fill every instrument's price onto that timeline (this is how
         we get a price at every second, even if the real data only has ticks
         every few seconds).
      4. Walk through the timeline second by second, asking the strategy for
         orders, applying them to the portfolio, and recording mark-to-market PnL.
      5. At the end of the day, close every open position.

    """

    def __init__(self, data_root, underliers, strategy):
        self.data_root = data_root
        self.underliers = underliers
        self.strategy = strategy
        self.portfolio = PortfolioTracker()

    def run(self):
        trading_dates = get_trading_dates(self.data_root)

        for date in trading_dates:
            print(f"Running backtest for {date} ...")
            self.run_one_day(date)

        return self.portfolio

    def run_one_day(self, date):
        date_folder = os.path.join(self.data_root, f"NSE_{date}")

        session_start = pd.Timestamp(f"{date} {SESSION_START_TIME}")
        session_end = pd.Timestamp(f"{date} {SESSION_END_TIME}")
        session_grid = pd.date_range(session_start, session_end, freq=TICK_FREQUENCY)

        options_index = build_options_index_for_date(date_folder)

        # We load futures price for each underlier and put it on the 1-second grid
        futures_price_by_underlier = {}
        for underlier in self.underliers:
            futures_df = load_futures_for_date(date_folder, underlier)
            if futures_df.empty:
                print(f"  Skipping {underlier} on {date} - no futures data")
                continue

            futures_price_by_underlier[underlier] = futures_df["Price"].reindex(
                session_grid, method="ffill"
            )
            """
            here, we use ffill method where if there is no tick at time t, we take the
            latest available price before t
            """

            expiry = get_nearest_expiry(options_index, underlier, date)
            self.strategy.set_expiry_for_day(underlier, expiry)

        option_price_by_instrument = {}
        for instrument_name, meta in options_index.items():
            if meta["underlier"] not in self.underliers:
                continue

            option_df = load_csv(meta["filepath"])
            if option_df.empty:
                continue

            option_price_by_instrument[instrument_name] = option_df["Price"].reindex(
                session_grid, method="ffill"
            )


        for timestamp in session_grid:
            current_prices = self._prices_at(option_price_by_instrument, timestamp)

            for underlier in self.underliers:
                if underlier not in futures_price_by_underlier:
                    continue

                futures_price = futures_price_by_underlier[underlier].loc[timestamp]

                if pd.isna(futures_price):
                    continue

                orders = self.strategy.on_tick(
                    timestamp,
                    underlier,
                    futures_price,
                    options_index,
                    current_prices,
                    self.portfolio,
                )

                for order in orders:
                    self.portfolio.apply_fill(order)

            self.portfolio.mark_to_market(timestamp, current_prices)


        final_prices = self._prices_at(option_price_by_instrument, session_end)
        self.portfolio.close_all_positions(session_end, final_prices)
        self.portfolio.mark_to_market(session_end, final_prices)

    def _prices_at(self, option_price_by_instrument, timestamp):
        
        prices = {}
        for instrument_name, price_series in option_price_by_instrument.items():
            price = price_series.loc[timestamp]
            if pd.notna(price):
                prices[instrument_name] = price
        return prices