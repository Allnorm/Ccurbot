from telebot import types

import interlayer
import telebot
import utils as ut


def value_checker(amount):
    thousand = 1
    if amount[-1].lower() == "k" or amount[-1].lower() == "к":
        thousand = 1000
        amount = amount[:-1]
    if amount[-1].lower() == "m" or amount[-1].lower() == "м":
        thousand = 1000000
        amount = amount[:-1]
    try:
        return float(amount.replace(',', '.')) * thousand
    except (ValueError, TypeError, AttributeError):
        return None


rate_interlayer = interlayer.Interlayer()
utils = ut.Utils()
bot = telebot.TeleBot(utils.token)


def inline_error(inline_id, title, description):
    bot.answer_inline_query(inline_id, [telebot.types.InlineQueryResultArticle(
        id='ERROR', title=title,
        description=description,
        input_message_content=telebot.types.InputTextMessageContent(message_text="И зачем ты нажал на меня?"))])


def bot_name_checker(message):  # Crutch to prevent the bot from responding to other bots commands

    cmd_text = message.text.split()[0]

    if ("@" in cmd_text and "@" + bot.get_me().username in cmd_text) or not ("@" in cmd_text):
        return True
    else:
        return False


def inline_currencies_list(title, description):
    return [types.InlineQueryResultArticle(
        id="ERROR",
        title=title,
        description=description,
        input_message_content=types.InputTextMessageContent
        (message_text="И зачем ты нажал на меня?")), ] + \
                  [types.InlineQueryResultArticle(
                      id=key,
                      title=key,
                      description=value,
                      input_message_content=types.InputTextMessageContent(message_text="И зачем ты нажал на меня?"))
                      for key, value in rate_interlayer.parsed_currencies.items()]


def inline_result_list(current_currency_name, current_currency_amount, second_currency_name):

    inline_list = []
    for key, value in rate_interlayer.currency_counter(current_currency_name,
                                                       current_currency_amount, second_currency_name).items():
        message_text = f"{current_currency_amount} {current_currency_name} - это {value} {key.split()[0]}" \
            if value != 0 else "И зачем ты нажал на меня?"
        value = value if value != 0 else "Указанное значение слишком мало для конвертации"
        inline_list.append(types.InlineQueryResultArticle(
            id=key.split()[0],
            title=key,
            description=value,
            input_message_content=types.InputTextMessageContent(message_text=message_text)))

    return inline_list


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if bot_name_checker(message):
        bot.reply_to(message, "Привет, этот бот поможет конвертировать валюты.\n"
                              "Просто используйте его в режиме инлайн: `@ccur2bot 1200 RUB`,"
                              "`@ccur2bot 12k usd byn` или `@ccur2bot 0,8m kzt EU`\n"
                              "/values - посмотреть список доступных валют.\n"
                              "Создано Allnorm'ом. Код проекта доступен по ссылке: "
                              "https://github.com/Allnorm/Ccurbot", parse_mode="markdown")


@bot.inline_handler(lambda query: len(query.query) >= 0)
def query_text(inline_query):
    if utils.extract_arg(inline_query.query, 0) is None:
        inline_error(inline_query.id, "Поле ввода пустое",
                     "Требуется ввести 2 (3) аргумента - количество, "
                     "код исходной валюты (необязательно - код итоговой валюты)")
        return

    current_currency_amount = value_checker(utils.extract_arg(inline_query.query, 0))
    if current_currency_amount is None:
        inline_error(inline_query.id, "Неверный аргумент", "Первый аргумент не конвертируется в число")
        return

    if utils.extract_arg(inline_query.query, 1) is None:
        inline_error(inline_query.id, "Недостаточно аргументов",
                     "Требуется ввести 2 (3) аргумента - количество, код исходной валюты "
                     "(необязательно - код итоговой валюты)")
        return

    if utils.extract_arg(inline_query.query, 3) is not None:
        inline_error(inline_query.id, "Аргументов слишком много",
                     "Требуется ввести 2 (3) аргумента - количество, "
                     "код исходной валюты (необязательно - код итоговой валюты)")
        return

    current_currency_name = utils.extract_arg(inline_query.query, 1).upper()
    if not rate_interlayer.is_currency_exist(current_currency_name):
        bot.answer_inline_query(inline_query.id,
                                inline_currencies_list("Указанная валюта не найдена!",
                                                       "Все существующие в базе данных валюты представлены ниже:"))
        return

    if current_currency_amount >= 1:
        if current_currency_amount % int(current_currency_amount) == 0:
            current_currency_amount = int(current_currency_amount)

    if current_currency_amount <= 0:
        inline_error(inline_query.id, "Неверный аргумент",
                     "Значение количества валюты не может быть меньше или равно 0")
        return

    try:
        second_currency_name = utils.extract_arg(inline_query.query, 2).upper()
    except AttributeError:
        second_currency_name = ""

    answer_list = inline_result_list(current_currency_name, current_currency_amount, second_currency_name)
    if not answer_list:
        answer_list = inline_currencies_list("Указанная валюта не найдена!",
                                             "Все существующие в базе данных валюты представлены ниже:")
    bot.answer_inline_query(inline_query.id, answer_list)


@bot.message_handler(commands=['values'])
def currencies_list(message):

    if bot_name_checker(message):
        text = "Полный список валют представлен ниже:\n"
        for key, value in rate_interlayer.parsed_currencies.items():
            text += f"`{key} - {value}`\n"
        bot.reply_to(message, text, parse_mode='markdown')


bot.infinity_polling()
