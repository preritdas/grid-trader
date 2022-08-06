"""
Instantiate and manage various brokers. Creates standardized wrapper classes for each
broker, which are then instantiated and called by the main Executor class.
"""
# Non-local imports
import alpaca_trade_api as alpaca_api

# Project modules
import keys


# ---- Broker wrappers---- 

class _Alpaca:
    """
    Wrap all used functions in standardized form, to be called by
    the Executor class.
    """
    def __init__(self, api_key = None, secret_key = None, base_url = None):
        """
        If all values aren't based, a default object is generated using
        keys provided in keys.ini.
        """
        # If all values weren't provided, use keys.ini values
        if not all(locals().values()):
            api_key = keys.Alpaca.api_key
            secret_key = keys.Alpaca.api_secret
            base_url = keys.Alpaca.base_url

        # If no keys were provided in keys.ini
        if not any(locals.values()):
            raise Exception(
                "Attempted to instantiate an Alpaca object but "
                "found no API keys in keys.ini."
            )

        self.alpaca = alpaca_api.REST(api_key, secret_key, base_url)


    def account_equity(self) -> float:
        """
        Get the account's total equity/market value.
        """
        return float(self.alpaca.get_account().equity)
    

    def current_price(self, symbol: str) -> float:
        if len(symbol) == 6:  # if crypto asset
            return float(self.alpaca.get_latest_crypto_trade(symbol, 'CBSE').p)

        return float(self.alpaca.get_latest_trade(symbol))


    def buy(
        self, 
        symbol: str, 
        quantity: float = None, 
        notional: float = None,
        take_profit: float = None,
        stop_loss: float = None
    ):
        """
        Place a buy order.

        quantity and notional are mutually exclusive, but at least one of them 
        must be specified.
        """
        if quantity and notional:
            raise Exception(
                "Provide either quantity or notional, not both."
            )
        elif (not quantity and not notional):
            raise Exception(
                "You must provide either a quantity or notional value."
            )

        if quantity:
            self.alpaca.submit_order(
                symbol = symbol,
                qty = quantity,
                side = 'buy',
                take_profit = {"limit_price": str(take_profit)} if take_profit else None,
                stop_loss = {
                    "stop_price": str(stop_loss), 
                    "limit_price": f"{(stop_loss * 0.995):.2f}"
                } if stop_loss else None
            )

        elif notional:
            self.alpaca.submit_order(
                symbol = symbol,
                notional = notional,
                side = 'buy',
                take_profit = {"limit_price": str(take_profit)} if take_profit else None,
                stop_loss = {
                    "stop_price": str(stop_loss), 
                    "limit_price": f"{(stop_loss * 0.995):.2f}"
                } if stop_loss else None
            )


    def sell(
        self, 
        symbol: str, 
        quantity: float = None, 
        notional: float = None,
        take_profit: float = None,
        stop_loss: float = None
    ):
        """
        Place a sell order.

        quantity and notional are mutually exclusive, but at least one of them 
        must be specified.
        """
        if quantity and notional:
            raise Exception(
                "Provide either quantity or notional, not both."
            )
        elif (not quantity and not notional):
            raise Exception(
                "You must provide either a quantity or notional value."
            )

        if quantity:
            self.alpaca.submit_order(
                symbol = symbol, 
                qty = quantity, 
                side = 'sell',
                take_profit = {"limit_price": str(take_profit)} if take_profit else None,
                stop_loss = {
                    "stop_price": str(stop_loss), 
                    "limit_price": f"{(stop_loss * 1.005):.2f}"
                } if stop_loss else None
            )

        elif notional:
            self.alpaca.submit_order(
                symbol = symbol,
                notional = notional,
                side = 'sell',
                take_profit = {"limit_price": str(take_profit)} if take_profit else None,
                stop_loss = {
                    "stop_price": str(stop_loss), 
                    "limit_price": f"{(stop_loss * 1.005):.2f}"
                } if stop_loss else None
            )


# ---- Executor ----

broker_mappings: dict[str, object] = {
    'alpaca': _Alpaca
}

class Executor:
    """
    Standardized operations in accounts with various brokers. 
    """
    def __init__(self, broker: str):
        """
        If the broker provided is not supported, Exception is raised, 
        printing the names of all supported brokers.
        """
        if not broker.lower() in broker_mappings:
            raise Exception(
                "Invalid broker provided. Supported brokers are "
                f"{broker_mappings}."
            )

        # Instantiate correct broker object using mappings
        self.broker = broker_mappings[broker.lower()]()
        self.broker_name = broker.lower()


    def account_equity(self) -> float:
        """
        Get the account's total equity/market value.
        """
        return self.broker.account_equity()


    def current_price(self, symbol: str) -> float:
        """
        Return the current price of a symbol.
        """
        return self.broker.current_price(symbol)


    def buy(
        self, 
        symbol: str, 
        quantity: float = None, 
        notional: float = None,
        take_profit: float = None,
        stop_loss: float = None
    ):
        """
        Place a buy order.

        quantity and notional are mutually exclusive, but at least one of them 
        must be specified.
        """
        return self.broker.buy(symbol, quantity, notional, take_profit, stop_loss)


    def sell(
        self, 
        symbol: str, 
        quantity: float = None, 
        notional: float = None,
        take_profit: float = None,
        stop_loss: float = None
    ):
        """
        Place a sell order.

        quantity and notional are mutually exclusive, but at least one of them 
        must be specified.
        """
        return self.broker.sell(symbol, quantity, notional, take_profit, stop_loss)


# ---- Default executor ----

if keys.default_broker: executor = Executor(keys.default_broker)
else: executor = None

def create_executor(broker: str = None):
    if broker is None and executor is None:
        raise Exception(
            "No broker was provided, and based on the configuration of keys.ini, "
            "no default broker was detected."
        )

    if broker is not None: return executor(broker)
    if broker is None and executor: return executor
        