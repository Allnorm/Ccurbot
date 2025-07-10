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


def inline_currencies_list():
    wallet_list = "\n".join([f'{key} - {value}' for key, value in rate_interlayer.parsed_currencies.items()])
    return (
            [types.InlineQueryResultArticle(
                id="ERROR",
                title="Указанная валюта не найдена!",
                description="Нажмите, чтобы получить список всех доступных валют",
                input_message_content=types.InputTextMessageContent(
                    message_text=f"Список всех доступных валют:\n{wallet_list}"))]
    )


def inline_result_list(current_currency_name, current_currency_amount, second_currency_name):

    inline_list = []
    all_values_text = f'{current_currency_amount} {current_currency_name} - это:\n'
    formatted_amount = f"{current_currency_amount:,}".replace(",", " ")
    for key, value in rate_interlayer.currency_counter(current_currency_name,
                                                       current_currency_amount, second_currency_name).items():
        value_text = f"{value:,}".replace(",", " ")
        message_text = (f"{formatted_amount} {current_currency_name} "
                        f"- это <code>{value_text}</code> {key.split()[0]}") \
            if value != 0 else "И зачем ты нажал на меня?"
        if value != 0:
            emoji = '-'
            transformed_value = value / current_currency_amount
            if 0 < transformed_value < 0.7:
                emoji = '🪙'
            elif 0.7 <= transformed_value < 5:
                emoji = '⚖️'
            elif 5 <= transformed_value < 100:
                emoji = '🗞'
            elif 100 <= transformed_value < 500:
                emoji = '🧻'
            elif 500 <= transformed_value:
                emoji = '⚰️'
            all_values_text += f'{emoji} <code>{value_text}</code> {key}\n'
        else:
            value_text = "Указанное значение слишком мало для конвертации"
        inline_list.append(types.InlineQueryResultArticle(
            id=f"{current_currency_amount}_{current_currency_name}_{value_text}_{key.split()[0]}",
            title=key,
            description=value_text,
            input_message_content=types.InputTextMessageContent(message_text=message_text, parse_mode='html')))

    if not second_currency_name:
        return [types.InlineQueryResultArticle(
            id=f'{current_currency_name}_{current_currency_amount}_NOT_SECOND',
            title="Вторая валюта для конвертации не указана",
            description=f"Нажмите, чтобы получить список всех курсов или введите название второй валюты",
            input_message_content=types.InputTextMessageContent(message_text=all_values_text, parse_mode='html'))
        ]
    elif len(inline_list) > 50:
        return [types.InlineQueryResultArticle(
            id=f'{current_currency_name}_{current_currency_amount}_TOO_MUCH',
            title="В списке слишком много валютных курсов",
            description=f'Нажмите, чтобы получить список всех курсов или введите название второй валюты',
            input_message_content=types.InputTextMessageContent(message_text=all_values_text, parse_mode='html'))]
    elif len(inline_list) == 0:
        return inline_currencies_list()
    elif len(inline_list) == 1:
        return inline_list
    else:
        return [types.InlineQueryResultArticle(
            id=f'{current_currency_name}_{current_currency_amount}_FILTERED',
            title="Список всех валютных курсов",
            description=f"Нажмите, чтобы получить список всех курсов, соответствующих фильтру",
            input_message_content=types.InputTextMessageContent(message_text=all_values_text, parse_mode='html'))
        ] + inline_list


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if bot_name_checker(message):
        bot.reply_to(message, "Привет, этот бот поможет конвертировать валюты.\n"
                              "Просто используйте его в режиме инлайн: `@ccur2bot 1200 RUB`, "
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
        bot.answer_inline_query(inline_query.id, inline_currencies_list())
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
    bot.answer_inline_query(inline_query.id, answer_list)


@bot.message_handler(commands=['values'])
def currencies_list(message):

    if bot_name_checker(message):
        text = "Полный список валют представлен ниже:\n"
        for key, value in rate_interlayer.parsed_currencies.items():
            text += f"`{key} - {value}`\n"
        bot.reply_to(message, text, parse_mode='markdown')


bot.infinity_polling()
