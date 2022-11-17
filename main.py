import configparser
import importlib
import logging
import sys
import traceback
import interlayer

import telebot


def value_checker(amount):
    throusand = 1
    if amount[-1].lower() == "k" or amount[-1].lower() == "к":
        throusand = 1000
        amount = amount[:-1]
    if amount[-1].lower() == "m" or amount[-1].lower() == "м":
        throusand = 1000000
        amount = amount[:-1]
    try:
        return float(amount.replace(',', '.')) * throusand
    except (ValueError, TypeError, AttributeError):
        return None


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


def token():

    config = configparser.ConfigParser()

    try:
        config.read("ccurbot.ini")
        tok = config["Ccurbot"]["token"]
        if tok == "":
            logging.error("Token is unknown! Bot will close!")
            sys.exit(1)
    except Exception as e:
        logging.error(str(e) + "\n" + traceback.format_exc())
        logging.error("incorrect config file! Bot will close!")
        sys.exit(1)

    return tok


logger_init()
rate_interlayer = interlayer.Interlayer()
bot = telebot.TeleBot(token())
version = "1.0"
built_date = "17.11.2022"
logging.info(f"###CCURBOT {version} (built date {built_date}) HAS BEEN STARTED###")


def inline_error(inline_id, title, description):
    bot.answer_inline_query(inline_id, [telebot.types.InlineQueryResultArticle(
            id='ERROR', title=title,
            description=description,
            input_message_content=telebot.types.InputTextMessageContent(message_text="И зачем ты нажал на меня?"))])


def botname_checker(message):  # Crutch to prevent the bot from responding to other bots commands

    cmd_text = message.text.split()[0]

    if ("@" in cmd_text and "@" + bot.get_me().username in cmd_text) or not ("@" in cmd_text):
        return True
    else:
        return False


@bot.message_handler(commands=['start'])
def send_welcome(message):

    if botname_checker(message):
        bot.reply_to(message, "Привет, этот бот поможет конвертировать валюты.\n"
                              "Просто используйте его в чате: `@ccur2bot 1200 RUB`"
                              "\nСоздано Allnorm'ом.", parse_mode="markdown")


@bot.inline_handler(lambda query: len(query.query) >= 0)
def query_text(inline_query):

    if interlayer.extract_arg(inline_query.query, 0) is None:
        inline_error(inline_query.id, "Поле ввода пустое",
                     "Требуется ввести 2 (3) аргумента - количество, "
                     "код исходной валюты (необязательно - код итоговой валюты)")
        return

    current_valute_amount = value_checker(interlayer.extract_arg(inline_query.query, 0))
    if current_valute_amount is None:
        inline_error(inline_query.id, "Неверный аргумент", "Первый аргумент не конвертируется в число")
        return

    if interlayer.extract_arg(inline_query.query, 1) is None:
        inline_error(inline_query.id, "Недостаточно аргументов",
                     "Требуется ввести 2 (3) аргумента - количество, код исходной валюты "
                     "(необязательно - код итоговой валюты)")
        return

    if interlayer.extract_arg(inline_query.query, 3) is not None:
        inline_error(inline_query.id, "Аргументов слишком много",
                     "Требуется ввести 2 (3) аргумента - количество, "
                     "код исходной валюты (необязательно - код итоговой валюты)")
        return

    current_valute_name = interlayer.extract_arg(inline_query.query, 1).upper()
    if not rate_interlayer.is_valute_exist(current_valute_name):
        bot.answer_inline_query(inline_query.id,
                                rate_interlayer.hint("Указанная валюта не найдена!",
                                                     "Все существующие в базе данных валюты представлены ниже:"))
        return

    if current_valute_amount >= 1:
        if current_valute_amount % int(current_valute_amount) == 0:
            current_valute_amount = int(current_valute_amount)

    if current_valute_amount <= 0:
        inline_error(inline_query.id, "Неверный аргумент",
                     "Значение количества валюты не может быть меньше или равно 0")
        return

    try:
        second_valute_name = interlayer.extract_arg(inline_query.query, 2).upper()
    except AttributeError:
        second_valute_name = ""

    answer_list = rate_interlayer.valute_counter(current_valute_name, current_valute_amount, second_valute_name)
    bot.answer_inline_query(inline_query.id, answer_list)


bot.infinity_polling()
