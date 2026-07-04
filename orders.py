from dataclasses import dataclass

@dataclass
class Order:
    """
    Made a simple data structure so that strategy and portfolio can communicate easily
    by directly passing this Order object.
    """
    instrument: str      # eg:"NIFTY22110314550PE" 
    side: str            # only two values, buy or sell
    price: float        
    quantity: int        # always = 1 in the project
    timestamp: object    
    underlier: str        

""" The buy_order and sell_order just ensure that startegy.py doen't need to again iterate 
 if we are buying or selling"""

def buy_order(instrument, price, timestamp, underlier, quantity=1):
    
    return Order(
        instrument=instrument,
        side="BUY",
        price=price,
        quantity=quantity,
        timestamp=timestamp,
        underlier=underlier,
    )


def sell_order(instrument, price, timestamp, underlier, quantity=1):
    return Order(
        instrument=instrument,
        side="SELL",
        price=price,
        quantity=quantity,
        timestamp=timestamp,
        underlier=underlier,
    )