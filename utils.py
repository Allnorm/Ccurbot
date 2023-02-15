import configparser
import importlib
import logging
import sys
import traceback


class Utils:

    def __init__(self):
        self.logger_init()
        self._token = self.set_token()
        version = "1.1"
        built_date = "15.02.2022"
        logging.info(f"###CCURBOT for SF {version} (built date {built_date}) HAS BEEN STARTED###")

    @staticmethod
    def logger_init():
        importlib.reload(logging)
        logging.basicConfig(
            handlers=[
                logging.FileHandler("ccurbot.log", 'w', 'utf-8'),
                logging.StreamHandler(sys.stdout)
            ],
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt="%d-%m-%Y %H:%M:%S")

    @staticmethod
    def set_token():

        config = configparser.ConfigParser()

        try:
            config.read("ccurbot.ini")
            token = config["Ccurbot"]["token"]
            if token == "":
                logging.error("Token is unknown! Bot will close!")
                sys.exit(1)
        except Exception as e:
            logging.error(str(e) + "\n" + traceback.format_exc())
            logging.error("incorrect config file! Bot will close!")
            sys.exit(1)

        return token

    @staticmethod
    def extract_arg(text, num):
        try:
            return str(text.split()[num])
        except IndexError:
            pass

    @property
    def token(self):
        return self._token
