"""
Defines the main GridTrader class along with a `create_default_bot` function
to instantiate GridTrader with primarily default values.
"""
# Local imports
import math
import multiprocessing as mp
import time  # sleep between trade logic

# Project modules
import utils
import brokers


class GridTrader:
    """
    Independent class which relies only on the Alpaca API instantiated globally.
    Requires a symbol, trading range, number of grids, and account allocation/quantity.
    If a quantity is given and it is not divisible by the number of grids, the per-grid
    order size will be rounded up to the nearest non-fractional order.

    If you want to use an account different to the one specified in keys.ini,
    you can pass in your own Alpaca API REST object. Do this if you'd 
    like to run multiple GridTraders simultaneously in different accounts.

    Grid safety is optional. `top_profit_stop` and `bottom_profit_stop` will default
    to one grid length above the grid if arguments aren't given.

    It's recommended to deploy Grid Traders using multiprocessing. 
    """
    def __init__(
        self, 
        symbol: str, 
        trading_range: tuple,
        grids_amount: int, 
        broker: str = None,
        account_allocation: float = None,
        quantity: int = None, 
        top_profit_stop: float = None,
        bottom_profit_stop: float = None,
    ):
        # Exception if trading_range items aren't numbers
        if any(
            item for item in trading_range if not \
                isinstance(item, int) and not isinstance(item, float)
        ):
            raise Exception("Items in the trading_range tuple must be numbers.")

        # Exception if invalid asset class is given
        if self.asset_class not in {'stock', 'crypto'}:
            raise Exception("Invalid asset class given.")

        # Instantiate broker
        if broker is None and brokers.executor:
            self.executor = brokers.executor
        elif broker is None and not brokers.executor:
            raise Exception(
                "You didn't provide a broker and a default broker couldn't "
                "be ascertained based on your keys.ini configuration."
            )

        # Create broker executor
        self.executor = brokers.create_executor(broker)

        # Trading range
        self.symbol = symbol.upper()
        self.range_bottom = trading_range[0]
        self.range_top = trading_range[1]
        self.grids_amount = grids_amount

        # Store starting account balance
        self.account_equity = self.executor.account_equity()

        # Account allocation - check for mutual exclusivity
        if account_allocation is not None and quantity is None:
            self.account_allocation = account_allocation
            self.position_size = account_allocation / self.grids_amount
            self.quantity = None
        elif quantity is not None and account_allocation is None:
            self.quantity = math.ceil(quantity / self.grids_amount)
            self.account_allocation = None
            self.position_size = None
        else:
            raise Exception("quantity and account allocation are mutually exclusive.")

        # Calculate grids and store them in a list
        self.grids = []
        distance = (self.range_top - self.range_bottom) / (self.grids_amount - 1)
        for i in range(self.grids_amount):
            grid = self.range_bottom + (i * distance)
            self.grids.append(round(grid, 2))

        # Check that no two grids are the same
        if len(self.grids) != len(set(self.grids)):
            raise Exception(
                "Check parameters. Two or more grids are in the same location."
            )

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

    @classmethod
    def from_defaults(
        cls,
        symbol: str, 
        grid_height: float,
        broker: str = None,
        grids_amount: int = 21,
        quantity: int = None, 
        allocation: float = None
    ) -> "GridTrader":
        """
        Returns a GridTrader object with a grid formed symmetrically
        around the current price.
        """
        # Instantiate executor for broker
        executor = brokers.create_executor(broker)

        # Default arguments
        assert not (quantity is not None and allocation is not None)
        assert not (quantity is None and allocation is None)
        
        # Parameters - current price and symbol name
        current_price = executor.current_price(symbol)
        symbol = symbol.upper()

        # Current price
        trading_range = ((current_price - grid_height), (current_price + grid_height))

        # Create the bot
        if quantity:
            return cls(
                symbol = symbol,
                trading_range = trading_range,
                grids_amount = grids_amount,
                broker = broker,
                quantity = quantity
            )
        elif allocation:
            return cls(
                symbol = symbol,
                trading_range = trading_range,
                grids_amount = grids_amount,
                broker = broker,
                account_allocation = allocation
            )

    def place_order(self, direction: str, size: int):
        """
        Places an order to buy or sell. `direction` must be given as 'buy' or 'sell'.
        """
        direction = direction.lower()
        if self.account_allocation:  # if notional values
            if direction == 'buy':
                self.executor.buy(
                    symbol = self.symbol,
                    notional = size * self.account_equity * self.position_size,
                    take_profit = self.top_profit_stop,
                    stop_loss = self.bottom_profit_stop,
                )
            elif direction == 'sell':
                self.executor.sell(
                    symbol = self.symbol,
                    notional = size * self.account_equity * self.position_size,
                    take_profit = self.bottom_profit_stop,
                    stop_loss = self.top_profit_stop
                )
            else:
                raise Exception(f"Invalid direction: {direction}.")
            
            # Notional value print message.
            utils.console.log(f"{self.symbol} Order placed. {direction = }, {size = }.")

        elif self.quantity:  # integer contracts
            if direction == 'buy':
                self.executor.buy(
                    symbol = self.symbol,
                    qty = self.quantity,
                    take_profit = self.top_profit_stop,
                    stop_loss = self.bottom_profit_stop
                )
            elif direction == 'sell':
                self.executor.sell(
                    symbol = self.symbol,
                    qty = self.quantity,
                    take_profit = self.bottom_profit_stop,
                    stop_loss = self.top_profit_stop
                )
            else:
                raise Exception(f"Invalid direction: {direction}.")
            
            # Quantity print message.
            utils.console.log(
                f"{self.symbol} Order placed. {direction = },", 
                f"quantity = {self.quantity}."
            )


    def trade_logic(self):
        """
        Internal function. This shouldn't be called.
        It's used by self.deploy(). This function is written to handle one iteration.
        
        Returns None if the current price is out of the grid's range.
        Returns True if the logic resulted in a buy.
        Returns False if the logic resulted in a short. 
        """
        current_price = self.executor.current_price(self.symbol)

        # Do nothing if price isn't in the grids
        if current_price < self.range_bottom or current_price > self.range_top:
            return None
        
        # Calculate grids below 
        grids_below = [grid for grid in self.grids if grid < current_price]

        # First iteration check
        if self.grids_below is None: self.grids_below = grids_below

        # Make a purchase decision
        len_grids_below, len_last_grids_below = len(grids_below), len(self.grids_below)
        if len_grids_below < len_last_grids_below:
            utils.console.print(grids_below)  # DEBUG
            order_args = ('buy', len_last_grids_below - len_grids_below)
            mp.Process(target = self.place_order, args = order_args).start()
        elif len_grids_below > len_last_grids_below:
            utils.console.print(grids_below)  # DEBUG
            order_args = ('sell', len_grids_below - len_last_grids_below)
            mp.Process(target = self.place_order, args = order_args).start()

        # Store grids below for next iteration
        self.grids_below = grids_below


    def deploy(self):
        """
        Deploys the Grid Trader. Iterates trade_logic.
        """
        utils.console.log(f"{self.symbol} Grid Trader has been deployed.")
        while True: 
            self.trade_logic()
            time.sleep(0.5)
