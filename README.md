# Grid Trader

A semi-automatic stock and crypto grid trader. 

Sample deployment for one asset:

```python
def main():
    """Deploys a Bitcoin grid trader."""
    btc_trader = GridTrader(
        symbol = 'BTCUSD',
        trading_range = (41800, 42400),
        grids_amount = 31,
        account_allocation = 0.5,
        asset_class = 'crypto'
    )

    # Deploy one bot locally
    btc_trader.deploy()
    # Use multiprocessing to allow multiple simultaneous bots
    mp.Process(target=btc_trader.deploy).start()
```

## Features

All features listed below are fully functional.

### Simultaneous Deployment

Multiple grid traders (for the same or different assets) can be deployed simultaneously, using different cores (multiprocessing). This allows each individual bot to run with a full performance capacity. 

It's recommended to leave two cores free per grid trader, because a grid trader sends off order execution tasks to another core to allow it continue actively trading unhindered. 

Below is an example of creating and running two bots simultaneous in individual cores.

```python
def main():
    """Top level main execution function."""
    # Deploy Bitcoin
    btc_trader = GridTrader(
        symbol = 'BTCUSD',
        trading_range = (41800, 42400),
        grids_amount = 31,
        account_allocation = 0.5,
        asset_class = 'crypto'
    )
    mp.Process(target = btc_trader.deploy).start()

    # Deploy Ethereum with default
    eth_trader = create_default_bot(
        symbol = 'ETHUSD',
        grid_height = 75,
        grids_amount = 15,
        quantity = 7
    )
    mp.Process(target = eth_trader.deploy).start()
```

Grid traders print order information to console when they place trades. This still works with multiprocessing.

![Deployment Screenshot](readme-content/deployment-sc.png)