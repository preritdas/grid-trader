# Local imports
import multiprocessing as mp

# Project modules
import gridtrader


def main():
    """Top level main execution function."""
    eth_trader = gridtrader.GridTrader(
        symbol = 'ETHUSD',
        trading_range = (2950, 2975),
        grids_amount = 26,
        quantity = 26,
        asset_class = 'crypto'
    )

    btc_trader = gridtrader.GridTrader(
        symbol = 'BTCUSD',
        trading_range = (15200, 15300),
        grids_amount = 51,
        quantity = 51,
        asset_class = 'crypto'
    )

    # Start the GridTraders simultaneously
    mp.Process(target=eth_trader.deploy).start()
    mp.Process(target=btc_trader.deploy).start()


if __name__ == "__main__":
    main()
