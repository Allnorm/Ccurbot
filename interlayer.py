import datetime
import logging
import sys
import traceback
import xml.etree.ElementTree

import certifi
import urllib3

from telebot import types


def extract_arg(text, num):
    try:
        return str(text.split()[num])
    except IndexError:
        pass


def rate_counter(current_valute_rate, current_valute_amount, next_valute_rate):
    return current_valute_rate / next_valute_rate * current_valute_amount


class Interlayer:
    RATE_REPO = "http://www.cbr.ru/scripts/XML_daily.asp"
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y")
    current_valute_rate = 0

    def __init__(self):
        self.root = None
        self.update_rate()

    def update_rate(self):

        http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
        try:
            r = http.request('GET', self.RATE_REPO)
            logging.info("exchange rate file downloaded successful from repository " + self.RATE_REPO)
        except Exception as e:
            logging.error(
                "impossible to download exchange rate file! You can try download it manually. Bot will close.")
            logging.error(str(e) + "\n" + traceback.format_exc())
            sys.exit(1)
        if r.status != 200:
            logging.error("impossible to download exchange rate file (http status = {})! "
                          "You can try download it manually. Bot will close.".format(r.status))
            sys.exit(1)
        try:
            f = open('rate.xml', 'wb')
            f.write(r.data)
            f.close()
        except IOError as e:
            logging.error("impossible to update exchange rate file! Bot will close")
            logging.error(str(e) + "\n" + traceback.format_exc())
            sys.exit(1)

        self.root = xml.etree.ElementTree.parse("rate.xml").getroot()
        logging.info("rate.xml updated successful")

    def is_valute_exist(self, current_valute_name):

        self.current_valute_rate = 1 if current_valute_name == "RUB" else 0
        for child in self.root:
            if child.find("CharCode").text.upper() == current_valute_name:
                self.current_valute_rate = float(child.find("Value").
                                                 text.replace(',', '.')) / int(child.find("Nominal")
                                                                               .text.replace(',', '.'))
        if self.current_valute_rate == 0:
            return False

        return True

    def valute_counter(self, current_valute_name, current_valute_amount):

        if datetime.datetime.now().strftime("%d-%m-%Y") != self.timestamp:
            self.update_rate()
            self.timestamp = datetime.datetime.now().strftime("%d-%m-%Y")

        answer_list = []

        if current_valute_name != "RUB":
            valute_result = round(rate_counter(self.current_valute_rate, current_valute_amount, 1), 2)
            answer_list.append(types.InlineQueryResultArticle(
                id="RUB",
                title="RUB - Российский рубль",
                description=valute_result,
                input_message_content=types.InputTextMessageContent
                (message_text="{} {} - это {} {}".format(current_valute_amount,
                                                         current_valute_name, valute_result, "RUB"))))

        for child in self.root:
            if child.find("CharCode").text == current_valute_name:
                continue

            next_valute_rate = float(child.find("Value").text.replace(',', '.')) / int(child.find("Nominal")
                                                                                       .text.replace(',', '.'))

            valute_result = round(rate_counter(self.current_valute_rate,
                                               current_valute_amount, next_valute_rate), 2)
            if valute_result >= 1:
                if valute_result % int(valute_result) == 0:
                    valute_result = int(valute_result)

            answer_list.append(types.InlineQueryResultArticle(
                id=child.find("CharCode").text,
                title="{} - {}".format(child.find("CharCode").text, format(child.find("Name").text)),
                description=valute_result,
                input_message_content=types.InputTextMessageContent
                (message_text="{} {} - это {} {}".format(current_valute_amount,
                                                         current_valute_name, valute_result,
                                                         child.find("CharCode").text))))

        return answer_list

    def hint(self, title, description):
        answer_list = [types.InlineQueryResultArticle(
            id="ERROR",
            title=title,
            description=description,
            input_message_content=types.InputTextMessageContent
            (message_text="И зачем ты нажал на меня?")),
            types.InlineQueryResultArticle(
            id="RUB",
            title="RUB",
            description="Российский рубль",
            input_message_content=types.InputTextMessageContent(message_text="И зачем ты нажал на меня?"))]

        for child in self.root:

            answer_list.append(types.InlineQueryResultArticle(
                id=child.find("CharCode").text,
                title=child.find("CharCode").text,
                description=child.find("Name").text,
                input_message_content=types.InputTextMessageContent(message_text="И зачем ты нажал на меня?")))

        return answer_list
