import datetime
import logging
import sys
import traceback

import requests


class Interlayer:
    RATE_REPO = "https://www.cbr-xml-daily.ru/daily_json.js"
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y")
    current_currency_rate = 0
    _currencies_list = []
    _parsed_currencies = {}

    def __init__(self):

        try:
            self.update_rate()
        except Exception as e:
            logging.error("Impossible to download exchange rates! Bot will close.")
            logging.error(str(e) + "\n" + traceback.format_exc())
            sys.exit(1)

    @staticmethod
    def rate_counter(current_currency_rate, current_currency_amount, next_currency_rate):
        return current_currency_rate / next_currency_rate * current_currency_amount

    def update_rate(self):

        curse_data = requests.get(self.RATE_REPO)
        if curse_data.status_code != 200:
            raise ConnectionRefusedError(f"HTTP status = {curse_data.status_code})!")
        self._currencies_list = [i[1] for i in curse_data.json().get("Valute").items()]
        self._parsed_currencies = {"RUB": "Российский рубль"}
        self._parsed_currencies.update({vault.get("CharCode"): vault.get("Name") for vault in self._currencies_list})
        logging.info("Currencies updated successful from repository " + self.RATE_REPO)

    def is_currency_exist(self, current_currency_name):

        self.current_currency_rate = 1 if current_currency_name == "RUB" else 0
        for vault in self._currencies_list:
            if vault.get("CharCode").upper() == current_currency_name:
                self.current_currency_rate = float(vault.get("Value")) / int(vault.get("Nominal"))
        if self.current_currency_rate == 0:
            return False

        return True

    def currency_counter(self, current_currency_name, current_currency_amount, second_currency_name):

        if datetime.datetime.now().strftime("%d-%m-%Y") != self.timestamp:
            try:
                self.update_rate()
            except Exception as e:
                logging.error("Impossible to download exchange rates! I will use my cache!")
                logging.error(str(e) + "\n" + traceback.format_exc())
            self.timestamp = datetime.datetime.now().strftime("%d-%m-%Y")

        answer_list = {}

        if current_currency_name != "RUB" and second_currency_name in "RUB":
            currency_result = round(self.rate_counter(self.current_currency_rate, current_currency_amount, 1), 2)

            if currency_result >= 1:
                if currency_result % int(currency_result) == 0:
                    currency_result = int(currency_result)

            answer_list.update({"RUB - Российский рубль": currency_result})

        for vault in self._currencies_list:
            if vault.get("CharCode") == current_currency_name or second_currency_name not in vault.get("CharCode"):
                continue
            next_currency_rate = float(vault.get("Value")) / int(vault.get("Nominal"))
            currency_result = round(self.rate_counter(self.current_currency_rate,
                                                      current_currency_amount, next_currency_rate), 2)
            if currency_result >= 1:
                if currency_result % int(currency_result) == 0:
                    currency_result = int(currency_result)

            answer_list.update({f"{vault.get('CharCode')} - {vault.get('Name')}": currency_result})

        return answer_list

    @property
    def parsed_currencies(self):
        return self._parsed_currencies
