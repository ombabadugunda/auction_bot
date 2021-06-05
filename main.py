import config
import telebot
from telebot import types, TeleBot
import random
import time

bot: TeleBot = telebot.TeleBot(config.token)

bot.message_handler(commands=['start'])


def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in ['Ok, let`s do this!']])
    bot.send_message(message.chat.id, 'Test message', reply_markup=keyboard)


bot.polling()
