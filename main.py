import telebot
import os
import logging
from config import *
from telebot import types
from flask import Flask, request
from Order import Order, User

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

order = Order()
user = User()
order_message = ""

@bot.message_handler(commands=['start', 'привет'])
def start(message):
    # Вот создание кнопки, можете поменять некоторые значения, и посмотреть что будет
    markup_inline = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton(text='Заказать Эвакуатор', callback_data='evocuator')
    item2 = types.InlineKeyboardButton(text='Заказать Манипулятор', callback_data='manipulator')
    markup_inline.add(item1, item2)
    # Здесь идет текст, который сопрождает кнопки, можно и без него
    bot.send_message(message.chat.id, f'Здравствуйте, {message.from_user.username}!\nЯ бот для заказа эвакуатора или манипулятора.\nЦена подачи 2500руб, если вас устраивает цена, то давайте оформим заявку, выберите услугу', reply_markup=markup_inline)

#перенаправление входящих сообщений с сервера фласк к боту
@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    #получаем данные от сервера в json, декодируем и отправляем боту
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@bot.callback_query_handler(func=lambda call:True)
def callback(call):
    if call.message:

        if call.data=='evocuator' or call.data == 'manipulator':
            msg = bot.send_message(call.message.chat.id, 'Что везем?')
            bot.register_next_step_handler(msg, ask_start_localtion)
        if call.data == 'yes':
            bot.send_message(call.message.chat.id, 'Спасибо за заказ, в ближайшее время с вами свяжется водитель')
            bot.send_message('-632179510',
                             f'<b>Поступил заказ от {call.message.from_user.username}</b>\nНомер телефона заказчика: {user.phone_number}\n' + order_message, parse_mode='HTML')
        if call.data == 'no':
            start(call.message)

def ask_start_localtion(message):
    msg = bot.send_message(message.chat.id, 'Откуда везем?')
    order.cargo = message.text
    telebot.logger.info("order.cargo = message.text")
    #keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    #button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    #keyboard.add(button_geo)
    #bot.send_message(message.chat.id, "Поделись местоположением", reply_markup=keyboard)

    bot.register_next_step_handler(msg, ask_end_localtion)

def ask_end_localtion(message):
    msg = bot.send_message(message.chat.id, 'Куда везем?')
    order.start_point = message.text
    bot.register_next_step_handler(msg, ask_phone_number)

def ask_phone_number(message):
    order.end_point = message.text
    msg = bot.send_message(message.chat.id, 'Ваш номер телефона, по которому мы сможем с вами связаться:')
    bot.register_next_step_handler(msg, result_price)

def result_price(message):
    user.phone_number = message.text
    #markup_inline = types.InlineKeyboardMarkup(row_width=1)
    #item1 = types.InlineKeyboardButton(text='Да, верно', callback_data='yes')
    #item2 = types.InlineKeyboardButton(text='Нет, надо исправить', callback_data='no')

    order_message = f'Груз: {order.cargo}\nГрузим по адресу: {order.start_point}\nВезем по адресу: {order.end_point}.'
    bot.send_message(message.chat.id, f'<b>Спасибо за заказ, в ближайшее время с вами свяжется водитель</b>\nВаш номер телефона: {user.phone_number}\n' + order_message, parse_mode='HTML')
    bot.send_message('-632179510',
                     f'<b>Поступил заказ от {message.from_user.username}</b>\nНомер телефона заказчика: {user.phone_number}\n' + order_message,
                     parse_mode='HTML')
    #markup_inline.add(item1, item2)
    #bot.send_message(message.chat.id, 'Верно?', reply_markup=markup_inline)

def get_address_from_coords(coords):
    #заполняем параметры, которые описывались выже. Впиши в поле apikey свой токен!
    PARAMS = {
        "apikey":"1c0b43e4-07c5-4773-bee4-d5217ffadfdc",
        "format":"json",
        "lang":"ru_RU",
        "kind":"house",
        "geocode": coords
    }

    #отправляем запрос по адресу геокодера.
    try:
        r = requests.get(url="https://geocode-maps.yandex.ru/1.x/", params=PARAMS)
        #получаем данные
        json_data = r.json()
        #вытаскиваем из всего пришедшего json именно строку с полным адресом.
        address_str = json_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["AddressDetails"]["Country"]["AddressLine"]
        #возвращаем полученный адрес
        return address_str
    except Exception as e:
        #если не смогли, то возвращаем ошибку
        return "error"

bot.polling(none_stop=True)
