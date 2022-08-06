"""
Instantiate and manage various brokers.
"""
# Non-local imports
import alpaca_trade_api as alpaca_api

# Project modules
import keys


# ---- Broker wrappers---- 

class Alpaca:
    """
    Wrap basic functions.
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

        self.alpaca = alpaca_api.REST(api_key, secret_key, base_url)
    
    def current_price(self, symbol: str) -> float:
        if len(symbol) == 6:  # if crypto asset
            return float(self.alpaca.get_latest_crypto_trade().p)

        return float(self.alpaca.get_latest_trade(symbol))

    def buy(self, symbol: str, quantity: float = None, notional: float = None):
        """
        Buy symbol in either quantity or notional value.

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
                side = 'buy'
            )
        elif notional:
            self.alpaca.submit_order(
                symbol = symbol,
                notional = notional,
                side = 'buy'
            )

    def sell(self, symbol: str, quantity: float = None, notional: float = None):
        """
        Buy symbol in either quantity or notional value.

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
            self.alpaca.submit_order(symbol = symbol, qty = quantity, side = 'sell')
        elif notional:
            self.alpaca.submit_order(symbol = symbol, notional = notional, side = 'sell')


# ---- Executor ----

broker_mappings: dict[str, object] = {
    'alpaca': Alpaca
}

class Executor:
    """
    Standardized operations in accounts with various brokers.
    """
    def __init__(self, broker: str):
        if not broker.lower() in broker_mappings:
            raise Exception(
                "Invalid broker provided. Supported brokers are "
                f"{broker_mappings}."
            )

        # Instantiate correct broker object using mappings
        self.broker = broker_mappings[broker.lower()]()
        self.broker_name = broker.lower()

    def current_price(self, symbol: str) -> float:
        """
        Return the current price of a symbol.
        """
        return self.broker.current_price(symbol)

    def buy(self, symbol: str, quantity: float = None, notional: float = None):
        """
        Place a buy order.
        """
        return self.broker.buy(symbol, quantity, notional)

    def sell(self, symbol: str, quantity: float = None, notional: float = None):
        """
        Place a sell order.
        """
        return self.broker.sell(symbol, quantity, notional)


# ---- Default executor ----

if keys.default_broker: executor = Executor(keys.default_broker)
else: executor = Executor('alpaca')
