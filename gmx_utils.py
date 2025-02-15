#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Snipermonke
"""


from web3 import Web3, AsyncWeb3
import yaml
import logging
import os
import json
import requests

base_dir = os.path.join(os.path.dirname(__file__))


logging.basicConfig(format='{asctime} {levelname}: {message}',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    style='{',
                    level=logging.INFO)


contract_map = {
    'arbitrum': {
        "eventemitter": {
            "contract_address": "0xC8ee91A54287DB53897056e12D9819156D3822Fb",
            "abi_path": "store/contracts/arbitrum/eventemitter.json"
        },
        "syntheticsreader":
        {
            "contract_address": "0x5Ca84c34a381434786738735265b9f3FD814b824",
            "abi_path": "store/contracts/arbitrum/syntheticsreader.json"
        },
        "datastore":
        {
            "contract_address": "0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8",
            "abi_path": "store/contracts/arbitrum/datastore.json"
        },
    },
    'avalanche': {
        "eventemitter": {
            "contract_address": "0xDb17B211c34240B014ab6d61d4A31FA0C0e20c26",
            "abi_path": "store/contracts/avalanche/eventemitter.json"
        },
    }
}


class ConfigManager:

    def __init__(self, chain: str):

        self.chain = chain
        self.rpc = None
        self.ws_rpc = None
        self.chain_id = None

    def set_config(self, filepath: str = os.path.join(base_dir, "config.yaml")):

        with open(filepath, 'r') as file:
            config_file = yaml.safe_load(file)

        self.set_rpc(config_file['rpcs'][self.chain])
        self.set_ws_rpc(config_file['ws_rpcs'][self.chain])
        self.set_chain_id(config_file['chain_ids'][self.chain])

    def set_rpc(self, value):
        self.rpc = value

    def set_ws_rpc(self, value):
        self.ws_rpc = value

    def set_chain_id(self, value):
        self.chain_id = value


async def create_connection(config):
    """
    Create a websocket connection to the blockchain
    """

    web3_obj = await AsyncWeb3(AsyncWeb3.WebSocketProvider(config.ws_rpc))

    return web3_obj


def create_https_connection(config):
    """
    Create a https connection to the blockchain
    """

    web3_obj = Web3(Web3.HTTPProvider(config.rpc))

    return web3_obj


def get_contract_object(web3_obj, contract_name: str, chain: str):
    """
    Using a contract name, retrieve the address and api from contract map
    and create a web3 contract object

    Parameters
    ----------
    web3_obj : web3_obj
        web3 connection.
    contract_name : str
        name of contract to use to map.
    chain : str
        arbitrum or avalanche.

    Returns
    -------
    contract_obj
        an instantied web3 contract object.

    """
    contract_address = contract_map[chain][contract_name]["contract_address"]

    contract_abi = json.load(
        open(
            os.path.join(
                base_dir,
                contract_map[chain][contract_name]["abi_path"]
            )
        )
    )
    return web3_obj.eth.contract(
        address=contract_address,
        abi=contract_abi
    )


def get_tokens_address_dict(chain: str):
    """
    Query the GMX infra api for to generate dictionary of tokens available on v2

    Parameters
    ----------
    chain : str
        avalanche of arbitrum.

    Returns
    -------
    token_address_dict : dict
        dictionary containing available tokens to trade on GMX.

    """
    url = {
        "arbitrum": "https://arbitrum-api.gmxinfra.io/tokens",
        "avalanche": "https://avalanche-api.gmxinfra.io/tokens"
    }

    try:
        response = requests.get(url[chain])

        # Check if the request was successful (status code 200)
        if response.status_code == 200:

            # Parse the JSON response
            token_infos = response.json()['tokens']
        else:
            print(f"Error: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {e}")

    token_address_dict = {}

    for token_info in token_infos:
        token_address_dict[token_info['address']] = token_info

    return token_address_dict


def get_reader_contract(config):
    """
    Get a reader contract web3_obj for a given chain

    Parameters
    ----------
    chain : str
        avalanche or arbitrum.

    """

    web3_obj = create_https_connection(config)
    return get_contract_object(
        web3_obj,
        'syntheticsreader',
        config.chain
    )


async def get_event_emitter_contract(config):
    """
    Get a event emitter contract web3_obj for a given chain

    Parameters
    ----------
    chain : str
        avalanche or arbitrum.

    """

    web3_obj = await create_connection(config)
    return get_contract_object(
        web3_obj,
        'eventemitter',
        config.chain
    )


if __name__ == "__main__":

    pass
