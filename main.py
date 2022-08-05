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
        trading_range = (22930, 23000),
        grids_amount = 51,
        account_allocation = 0.1,
        asset_class = 'crypto'
    )

    easy_deploy = gridtrader.create_default_bot(
        symbol = 'BTCUSD',
        grid_height = 15,
        grids_amount = 16,
        allocation = 0.5
    )

    # Start the manual GridTraders simultaneously
    mp.Process(target=eth_trader.deploy).start()
    mp.Process(target=btc_trader.deploy).start()


if __name__ == "__main__":
    main()
