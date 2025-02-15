#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Snipermonke
"""

import logging

from gmx_utils import (
    contract_map, get_tokens_address_dict, get_reader_contract, ConfigManager, base_dir
)

import json
import os
import time

from get_oracle_prices import OraclePrices


class GetMarkets:

    def __init__(self, config):

        self.config = config
        logging.info("Initialising markets data")

    def get_available_markets(self, use_archive=False):

        if use_archive:
            infile = os.path.join(base_dir,
                                  "store",
                                  "markets.json")

            with open(infile, "r") as json_file:
                markets = json.load(json_file)

            if self._check_file_age(infile):
                logging.warning("Archive more than 14 days old")
                logging.warning(
                    "Archive should be rerun regularly to ensure all markets are present"
                )
            return markets

        markets = self._process_markets()
        return markets

    def create_markets_archive(self):

        logging.info("Creating archive of markets")

        markets = self._process_markets()
        output_dir = os.path.join(base_dir, "store")

        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        outfile = os.path.join(output_dir, "markets.json")

        with open(outfile, "w") as json_file:
            json.dump(markets, json_file, indent=4)

        return markets

    def _get_available_markets_raw(self):

        reader_contract = get_reader_contract(self.config)
        data_store_contract_address = contract_map[self.config.chain]['datastore']['contract_address']

        return reader_contract.functions.getMarkets(data_store_contract_address, 0, 100).call()

    def _process_markets(self):
        """
        Call and process the raw market data

        Returns
        -------
        decoded_markets : dict
            dictionary decoded market data.

        """
        token_address_dict = get_tokens_address_dict(self.config.chain)
        raw_markets = self._get_available_markets_raw()

        decoded_markets = {}
        for raw_market in raw_markets:
            try:

                if not self._check_if_index_token_in_signed_prices_api(
                    raw_market[1]
                ):
                    continue
                market_symbol = token_address_dict[raw_market[1]]['symbol']

                if raw_market[2] == raw_market[3]:
                    market_symbol = f"{market_symbol} (Single Side)"

                is_synthetic = False
                if raw_market[1] != raw_market[2]:
                    is_synthetic = True

                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': market_symbol,
                    'index_token_address': raw_market[1],
                    'market_metadata': token_address_dict[raw_market[1]],
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3],
                    'is_synthetic': is_synthetic
                }
                if raw_market[0] == "0x0Cf1fb4d1FF67A3D8Ca92c9d6643F8F9be8e03E5":
                    decoded_markets[raw_market[0]]["market_symbol"] = "wstETH"
                    decoded_markets[raw_market[0]
                                    ]["index_token_address"] = "0x5979D7b546E38E414F7E9822514be443A4800529"

            # If KeyError it is because there is no market symbol and it is a
            # swap market
            except KeyError:
                if not self._check_if_index_token_in_signed_prices_api(
                    raw_market[1]
                ):
                    continue
                market_symbol = 'SWAP {}-{}'.format(
                    token_address_dict[raw_market[2]]['symbol'],
                    token_address_dict[raw_market[3]]['symbol']
                )
                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': market_symbol,
                    'index_token_address': raw_market[1],
                    'market_metadata': {'symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    )},
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }
            logging.info(f"Processed: {market_symbol}")

        return decoded_markets

    def _check_if_index_token_in_signed_prices_api(self, index_token_address):

        try:
            prices = OraclePrices(chain=self.config.chain).get_recent_prices()

            if index_token_address == "0x0000000000000000000000000000000000000000":
                return True
            prices[index_token_address]
            return True
        except KeyError:

            print("{} market not live on GMX yet..".format(index_token_address))
            return False

    @staticmethod
    def _check_file_age(filepath):

        # Get the file creation time
        creation_time = os.stat(filepath).st_ctime
        current_time = time.time()

        # Calculate the age of the file in days
        file_age_days = (current_time - creation_time) / (24 * 3600)

        # Check if the file is older than 14 days
        return file_age_days > 14


if __name__ == '__main__':

    config = ConfigManager(chain='arbitrum')
    config.set_config()
    markets = GetMarkets(config).get_available_markets(use_archive=True)
