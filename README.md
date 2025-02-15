# GMX Positions Monitor

Developed using:
```python
python=3.10.4
web3=7.7.0
```

Start by setting your rpc. HTTPS RPC goes under "rpcs" and websocket rpc under "ws_rpcs". Set for appropriate chain*.

```yaml
rpcs:
  arbitrum: arbitrum_rpc
  avalanche: avax_rpc
ws_rpcs:
  arbitrum: wss_rpc
  avalanche: avax_rpc_ws
chain_ids:
  arbitrum: 42161
  avalanche: 43114


```

To run, run the py script [monitor_positions_by_websocket.py](https://github.com/snipermonke01/gmx_positions_monitor/blob/main/monitor_positions_by_websocket.py):

```python
main(chain="arbitrum")
```

Notes:

- In [monitor_positions_by_websocket.py](https://github.com/snipermonke01/gmx_positions_monitor/blob/main/monitor_positions_by_websocket.py#L108) the latest markets not being fetched from the reader contract and instead are calling upon the [archive market json file](https://github.com/snipermonke01/gmx_positions_monitor/blob/main/store/markets.json) in the store directory. This means any new markets added to GMX since will not be included. To update this file, run the following method from the GetMarkets class in [get_markets.py](https://github.com/snipermonke01/gmx_positions_monitor/blob/main/get_markets.py#L20).

```python
config = ConfigManager(chain='arbitrum')
config.set_config()
markets = GetMarkets(config).create_markets_archive(use_archive=True)
```
 Alternatively, you can set use_archive to False here [monitor_positions_by_websocket.py](https://github.com/snipermonke01/gmx_positions_monitor/blob/main/monitor_positions_by_websocket.py#L108).

 - Avalanche chain not tested yet
 - [monitor_positions_by_block.py](https://github.com/snipermonke01/gmx_positions_monitor/blob/main/monitor_positions_by_block.py) is depreciated
