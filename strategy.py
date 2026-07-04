from data_utils import get_atm_strike_instrument
from orders import buy_order, sell_order


class Strategy:
    """
    The backtest_engine only calls on_tick() function so it doesn't matter what
    strategy is present, we can write a new Class with the same method and the
    backtest engine will work unchanged.
    """

    def on_tick(self, timestamp, underlier, futures_price, options_index, current_prices, portfolio):
        """
        Called once per tick for a given underlier.
        It returns a list of Order objects to execute this tick.
        """
        raise NotImplementedError("Subclasses must implement on_tick()")


class RollingStraddleStrategy(Strategy):
    """
    Implements the main strategy:
      - At each tick, find the strike closest to the futures price.
      - Hold  CE +  PE at that strike.
      - If the ATM strike changes, sell the old CE/PE and buy the new CE/PE.
    """

    def __init__(self):
        # Track, per underlier, which expiry we've locked in for the day e.g. {"NIFTY": "221103", "BANKNIFTY": "221103"}
        self.expiry_for_underlier = {}

        # Track, per underlier, which strike we currently hold a straddle on e.g. {"NIFTY": 18150}
        self.current_strike_for_underlier = {}

    def set_expiry_for_day(self, underlier, expiry):
        """Called once per day by the engine, after get_nearest_expiry() is resolved."""
        self.expiry_for_underlier[underlier] = expiry

        self.current_strike_for_underlier[underlier] = None

    def on_tick(self, timestamp, underlier, futures_price, options_index, current_prices, portfolio):
        expiry = self.expiry_for_underlier.get(underlier)
        if expiry is None:
            
            return []

        new_ce_instrument = get_atm_strike_instrument(
            options_index, underlier, expiry, futures_price, "CE"
        )
        new_pe_instrument = get_atm_strike_instrument(
            options_index, underlier, expiry, futures_price, "PE"
        )

        if new_ce_instrument is None or new_pe_instrument is None:
            return []

        new_strike = options_index[new_ce_instrument]["strike"]
        current_strike = self.current_strike_for_underlier.get(underlier)

        orders = []

        if current_strike == new_strike:
            # If the ATM strike is same, we do nothing
            return orders

        for instrument, position in list(portfolio.open_positions.items()):
            if position["underlier"] != underlier:
                continue

            exit_price = current_prices.get(instrument, position["entry_price"])
            orders.append(sell_order(instrument, exit_price, timestamp, underlier))

        
        ce_price = current_prices.get(new_ce_instrument)
        pe_price = current_prices.get(new_pe_instrument)

        if ce_price is not None:
            orders.append(buy_order(new_ce_instrument, ce_price, timestamp, underlier))

        if pe_price is not None:
            orders.append(buy_order(new_pe_instrument, pe_price, timestamp, underlier))

        # Remember the strike we now hold, so we don't re-trade next tick unnecessarily
        self.current_strike_for_underlier[underlier] = new_strike

        return orders