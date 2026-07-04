class PortfolioTracker:
    """
    The class keeps track of which instruments we currently hold a position in,
    every trade we've ever closed, with its realized PnL and a full history of PnL
    snapshots over time.

    As the class is independent of the strategy, we can allow several different strategies
    to use the same portfolio code.
     """

    def __init__(self):
        # open_positions is a dictionary:
        #   instrument_name -> {"entry_price": ..., "quantity": ..., "entry_time": ..., "underlier": ...}
        self.open_positions = {}

        # closed_trades is a list of dictionaries, one per completed trade
        self.closed_trades = []

        # pnl_history is a list of dictionaries, one per snapshot in time
        # e.g. {"timestamp": ..., "realized_pnl": ..., "unrealized_pnl": ..., "total_pnl": ...}
        self.pnl_history = []

        # running total of PnL from trades we have already closed
        self.realized_pnl = 0.0

    def apply_fill(self, order):
        """
        BUY always opens a new position while SELL closes an existing one and we always
        need to buy before we sell
        """
        if order.side == "BUY":
            self._open_position(order)
        elif order.side == "SELL":
            self._close_position(order)
        else:
            raise ValueError(f"Unknown order side: {order.side}")

# we use the key order_instrument eg: NIFTY22NOV18000CE for the open_posotions dict

    def _open_position(self, order):
        if order.instrument in self.open_positions:
            raise ValueError(
                f"Tried to open {order.instrument} but a position is already open. "
                f"Max position size is 1 per instrument."
            )

        self.open_positions[order.instrument] = {
            "entry_price": order.price,
            "quantity": order.quantity,
            "entry_time": order.timestamp,
            "underlier": order.underlier,
        }

    def _close_position(self, order):
        if order.instrument not in self.open_positions:
            raise ValueError(
                f"Tried to close {order.instrument} but no open position exists."
            )

        position = self.open_positions.pop(order.instrument)

        trade_pnl = (order.price - position["entry_price"]) * position["quantity"]
        self.realized_pnl += trade_pnl
        # here, quantity is always 1, and the trade_pnl = (current_price - entry_price)
        self.closed_trades.append({
            "instrument": order.instrument,
            "underlier": position["underlier"],
            "entry_time": position["entry_time"],
            "entry_price": position["entry_price"],
            "exit_time": order.timestamp,
            "exit_price": order.price,
            "quantity": position["quantity"],
            "pnl": trade_pnl,
        })

    def mark_to_market(self, timestamp, current_prices):
        """
        We compute the market value of all the open positions, i.e, the PnL we would 
        get if we sold all of them at this instant.

        If a price isn't available for some open instrument at this exact
        timestamp (e.g. no tick yet), that position's last known price is
        used instead of crashing the backtest.
        """
        unrealized_pnl = 0.0

        for instrument, position in self.open_positions.items():
            current_price = current_prices.get(instrument)
            if current_price is None:
                continue

            unrealized_pnl += (current_price - position["entry_price"]) * position["quantity"]

        total_pnl = self.realized_pnl + unrealized_pnl

        self.pnl_history.append({
            "timestamp": timestamp,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "open_positions": list(self.open_positions.keys()),
        })

        return total_pnl

    def close_all_positions(self, timestamp, current_prices):
        """
        At 3;30 pm, we need to close all positions and sell whatever we have
        """
        instruments_to_close = list(self.open_positions.keys())

        for instrument in instruments_to_close:
            position = self.open_positions[instrument]
            exit_price = current_prices.get(instrument, position["entry_price"])

            from orders import sell_order
            forced_sell = sell_order(
                instrument=instrument,
                price=exit_price,
                timestamp=timestamp,
                underlier=position["underlier"],
                quantity=position["quantity"],
            )
            self._close_position(forced_sell)

    def get_pnl_history_dataframe(self):
        # convert the list of dicts to a df so we can analyse
        import pandas as pd
        return pd.DataFrame(self.pnl_history)

    def get_closed_trades_dataframe(self):
        # convert the trade log to a df so we can analyse
        import pandas as pd
        return pd.DataFrame(self.closed_trades)