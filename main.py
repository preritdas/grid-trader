# Non-local imports
import alpaca_trade_api

# Local imports
import multiprocessing as mp
import time
import sys

# Project modules
import _keys


# Instantiate Alpaca API
alpaca = alpaca_trade_api.REST(
    key_id = _keys.alpaca_api_key,
    secret_key = _keys.alpaca_api_secret,
    base_url = _keys.alpaca_base_url
)


class GridTrader:
    """
    Independent class which relies only on the Alpaca API instantiated globally.
    Requires a symbol, trading range, number of grids, and account allocation.

    Grid safety is optional. `top_profit_stop` and `bottom_profit_stop` will default
    to one grid length above the grid if arguments aren't given.

    It's recommended to deploy Grid Traders using multiprocessing. 
    """

    def __init__(
        self, 
        symbol: str, 
        trading_range: tuple,
        grids_amount: int, 
        account_allocation: float, 
        top_profit_stop: float = None,
        bottom_profit_stop: float = None,
        asset_class: str = 'stock'
    ):
        # Exception if trading_range items aren't numbers
        for item in trading_range:
            if type(item) not in [int, float]:
                raise Exception("Items in the trading_range tuple must be numbers.")

        # Exception if invalid asset class is given
        self.asset_class = asset_class.lower()
        if self.asset_class != 'stock' and self.asset_class != 'crypto':
            raise Exception("Invalid asset class given.")

        self.symbol = symbol
        self.range_bottom = trading_range[0]
        self.range_top = trading_range[1]
        self.grids_amount = grids_amount
        # Account allocation
        self.account_allocation = account_allocation
        self.position_size = account_allocation / self.grids_amount

        # Calculate grids and store them in a list
        self.grids = []
        distance = (self.range_top - self.range_bottom) / (self.grids_amount - 1)
        for i in range(self.grids_amount):
            grid = self.range_bottom + (i * distance)
            self.grids.append(round(grid, 2))

        # Grid safety - top
        if top_profit_stop is None:
            self.top_profit_stop = self.range_top + distance
        else:
            self.top_profit_stop = top_profit_stop
        # Grid safety - bottom
        if bottom_profit_stop is None:
            self.bottom_profit_stop = self.range_bottom - distance
        else:
            self.bottom_profit_stop = bottom_profit_stop

        # Define self.grids_below to allow first trade_logic iteration 
        self.grids_below = None
    
    def current_price(self):
        """Returns the current price of self.symbol, calculated by the latest trade."""
        if self.asset_class == 'crypto':
            return float(alpaca.get_latest_crypto_trade(symbol = self.symbol, exchange = 'CBSE').p)
        else:
            return float(alpaca.get_snapshot(symbol = self.symbol).latest_trade.p)

    def place_order(self, direction: str, size: int):
        """
        Places an order to buy or sell. `direction` must be given as 'buy' or 'sell'.
        """
        direction = direction.lower()
        if direction == 'buy':
            alpaca.submit_order(
                symbol = self.symbol,
                notional = size * float(alpaca.get_account().equity) * self.position_size,
                side = 'buy',
                take_profit = {
                    "limit_price": self.top_profit_stop
                },
                stop_loss = {
                    "stop_price": self.bottom_profit_stop,
                    "limit_price": self.bottom_profit_stop * 0.995  # 0.5% lower
                }
            )
        elif direction == 'sell':
            alpaca.submit_order(
                symbol = self.symbol,
                notional = size * float(alpaca.get_account().equity) * self.position_size,
                side = 'sell',
                take_profit = {
                    "limit_price": self.bottom_profit_stop
                },
                stop_loss = {
                    "stop_price": self.top_profit_stop,
                    "limit_price": self.top_profit_stop * 1.005  # 0.5% higher
                }
            )
        else:
            raise Exception(f"Invalid direction: {direction}.")

        print(f"Order placed. {direction = }, {size = }.")

    def trade_logic(self):
        """
        Internal function. This shouldn't be called.
        It's used by self.deploy(). This function is written to handle one iteration.
        
        Returns None if the current price is out of the grid's range.
        Returns True if the logic resulted in a buy.
        Returns False if the logic resulted in a short. 
        """
        current_price = self.current_price()
        # End logic/return nothing if price isn't in the grids
        if current_price < self.range_bottom or current_price > self.range_top:
            print('Not in range.')
            return None
        
        # Calculate grids below 
        grids_below = [grid for grid in self.grids if grid < current_price]

        # First iteration check
        if self.grids_below is None:
            self.grids_below = grids_below

        # Make a purchase decision
        if len(grids_below) > len(self.grids_below):
            print(grids_below)  # DEBUG
            order_args = ('buy', len(grids_below) - len(self.grids_below))
            mp.Process(target = self.place_order, args = order_args).start()
        elif len(grids_below) < len(self.grids_below):
            print(grids_below)  # DEBUG
            order_args = ('sell', len(self.grids_below) - len(grids_below))
            mp.Process(target = self.place_order, args = order_args).start()
        else:
            print('waiting')

        # Store grids below for next iteration
        self.grids_below = grids_below

    def deploy(self):
        """
        Deploys the Grid Trader.
        Iterates trade_logic during market hours once per second due to rate limit.
        """
        while True:
            # if market is open:
            self.trade_logic()
            # time.sleep(0.61)


def main():
    """Top level main execution function."""
    btc_trader = GridTrader(
        symbol = 'BTCUSD',
        trading_range = (float(sys.argv[1]), float(sys.argv[2])),
        grids_amount = 21,
        account_allocation = 1,
        asset_class = 'crypto'
    )
    mp.Process(target = btc_trader.deploy).start()

if __name__ == "__main__":
    main()
