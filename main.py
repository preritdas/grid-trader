# Non-local imports
import alpaca_trade_api

# Local imports
import multiprocessing as mp

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

    It's recommended to deploy Grid Traders using multiprocessing. 
    """
    def __init__(self, symbol: str, trading_range: tuple, grids_amount: int, account_allocation: float):
        # Exception if trading_range items aren't numbers
        for item in trading_range:
            if type(item) not in [int, float]:
                raise Exception("Items in the trading_range tuple must be numbers.")

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
    
    def current_price(self):
        """Returns the current price of self.symbol, calculated by the latest trade."""
        return float(alpaca.get_snapshot(symbol = self.symbol).latest_trade.p)

    def place_order(self, direction: str):
        """
        Places an order to buy or sell. `direction` must be given as 'buy' or 'sell'.
        """
        # Check for valid direction input
        direction = direction.lower()
        if direction != 'buy' and direction != 'sell':
            raise Exception("Invalid argument for direction. Must be 'buy' or 'sell'.")

        # Place order with multiprocessing
        def submit_order():
            alpaca.submit_order(
                symbol = self.symbol,
                notional = float(alpaca.get_acccount().equity) * self.position_size,
                side = direction
            )

        # Submit the order with multiprocess 
        mp.Process(target = submit_order).start()

    def trade_logic(self):
        """
        Internal function. This shouldn't be called.
        It's used by self.deploy(). This function is written to handle one iteration.
        """
        current_price = self.current_price()
        # End logic/return nothing if price isn't in the grids
        if current_price < self.range_bottom or current_price > self.range_top:
            return None
        
        # Calculate grids below and above
        grids_below = [grid for grid in self.grids if grid < current_price]
        grids_above = [grid for grid in self.grids if grid > current_price]

    def deploy(self):
        """Deploys the Grid Trader."""
        # TESTING (run trade logic once instantly)
        self.trade_logic()

if __name__ == "__main__":
    grid_trader_demo = GridTrader('AAPL', (150, 200), 11, 0.5)
    grid_trader_demo.deploy()