import time
import logging

import asyncio

from numerize import numerize
from gmx_utils import get_event_emitter_contract, create_connection, ConfigManager, get_tokens_address_dict
from get_markets import GetMarkets
from web3 import Web3, AsyncWeb3


def initialize_config(chain='arbitrum'):
    config = ConfigManager(chain)
    config.set_config()
    return config


async def fetch_contract_events(contract_obj, from_block):
    logging.info(f"Listening for events from block: {from_block}")
    event_filter = await contract_obj.events.EventLog1.create_filter(from_block='latest')
    return event_filter


def generate_txn_link(chain, txn_hash):
    explorers = {'arbitrum': 'https://arbiscan.io/tx/',
                 'avalanche': 'https://snowtrace.io/tx/'}
    return f"{explorers.get(chain, '#')}{txn_hash.hex()}"


def generate_size_emoji(size_tuple):
    multiplication_factor_raw = size_tuple / 50000
    if multiplication_factor_raw < 1:
        return "\U0001fad0"
    multiplication_factor = round(multiplication_factor_raw)
    size_emoji = "\U0001fad0" * multiplication_factor
    return "\n".join([size_emoji[i:i + 10] for i in range(0, len(size_emoji), 10)])


def process_position(event, available_markets, config, position_type, tokens_api_dict):

    # User address
    account = event['args']['eventData']['addressItems']['items'][0]['value']

    # Index being traded
    gm_market_token = event['args']['eventData']['addressItems']['items'][1]['value']

    # Collateral token address
    collateral_token_address = event['args']['eventData']['addressItems']['items'][2]['value']

    # Decimals of collateral token
    collateral_token_decimals = tokens_api_dict[collateral_token_address]['decimals']

    # position size in USD
    position_size_usd = event['args']['eventData']['uintItems']['items'][12]['value'] / \
        1000000000000000000000000000000

    # collateral amount in tokens
    collateral_amount = event['args']['eventData']['uintItems']['items'][2]['value'] / \
        10 ** collateral_token_decimals

    # collateral token price in USD
    collateral_token_price = event['args']['eventData']['uintItems']['items'][10]['value'] / 10 ** (
        30 - collateral_token_decimals)

    collateral_usd_amount = collateral_amount * collateral_token_price

    # is long or short
    is_long = event['args']['eventData']['boolItems']['items'][0]['value']
    txn = generate_txn_link(config.chain, event['transactionHash'])

    position, position_emoji = (
        'Long', '\U0001F4C8') if is_long else ('Short', '\U0001F4C9')

    # get number emojis for text message
    size_emoji = generate_size_emoji(position_size_usd)
    txn_txt = "<a href='{}'>Txn Link</a>".format(txn)
    account_link_txt = "<a href='https://app.gmx.io/#/actions/{}'>Account</a>".format(
        account)

    if position_type == 'increase':
        message = "\U0001F7E2 Position Increased \U0001F7E2\n\n\U0001FA99 {}\n\U0001F4B0 Position Size: ${}\n{} {} x{:.2f}\n\U0001F517 {}\n\n{}\n\n{} | {}\n".format(
            available_markets[gm_market_token]['market_symbol'],
            numerize.numerize(position_size_usd),
            position_emoji,
            position,
            position_size_usd / collateral_usd_amount,
            config.chain.title(),
            size_emoji,
            txn_txt,
            account_link_txt)
    else:
        message = "\U0001F534 Position Decreased \U0001F534\n\n\U0001FA99 {}\n\U0001F4B0 Position Size: ${}\n{} {}\n\U0001F517 {}\n\n{}\n\n{} | {}\n".format(
            available_markets[gm_market_token]['market_symbol'],
            numerize.numerize(position_size_usd),
            position_emoji,
            position,
            config.chain.title(),
            size_emoji,
            txn_txt,
            account_link_txt)

    print(message)


async def main():
    logging.basicConfig(level=logging.INFO)
    config = initialize_config()
    available_markets = GetMarkets(config).get_available_markets(use_archive=True)
    tokens_api_dict = get_tokens_address_dict(config.chain)
    contract_obj = await get_event_emitter_contract(config)

    event_filter = await fetch_contract_events(contract_obj, 'latest')

    while True:
        try:
            for event in await event_filter.get_new_entries():
                event_name = event['args']['eventName']
                if event_name == 'PositionIncrease':
                    process_position(event, available_markets, config,
                                     'increase', tokens_api_dict)
                elif event_name == 'PositionDecrease':
                    process_position(event, available_markets, config,
                                     'decrease', tokens_api_dict)

        except KeyError as e:
            logging.error(e)
            time.sleep(1)
        else:
            pass


if __name__ == "__main__":
    asyncio.run(main())
