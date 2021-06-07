# -*- coding: utf-8 -*-

import config
import telebot
from telebot import types, TeleBot
import random
import time
import pyrebase

configFirebase = {
    "apiKey": "AIzaSyCSO1622ymqxT1S3VzgOzT5pFM8UTyBrTs",
    "authDomain": "auction-bot-56f9c.firebaseapp.com",
    "databaseURL": "https://auction-bot-56f9c-default-rtdb.europe-west1.firebasedatabase.app",
    "storageBucket": "auction-bot-56f9c.appspot.com"
}

firebase = pyrebase.initialize_app(configFirebase)
db = firebase.database()
bot: TeleBot = telebot.TeleBot(config.token)


def getAuctions():
    try:
        auctions = db.child("auctions").get()
        return list(auctions.val().keys())
    except:
        return ['Немає поточних аукціонів']


def getWorks(auction):
    try:
        work = db.child("auctions").child(auction).child('art').get()
        return list(work.val().keys())
    except:
        return ['Немає робіт']


def get_auction_by_name(name):
    auctions = db.child("auctions").get()
    auctions_dict = dict(auctions.val())
    for auction in auctions_dict:
        if auctions_dict[auction]['name'] == name:
            return auction


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.chat.id, 'Вітаю тебе! Я допоможу тобі придбати трохи мистецтва. '
                                      'Зараз ти можеш взяти учать в таких аукціонах:')
    buttons = []
    buttons.extend(getAuctions())
    try:
        buttons.remove('Немає поточних аукціонів')
    except:
        pass
    if message.chat.id == 54778970:
        buttons.append('Створити аукціон')
    keyboard.add(*[types.KeyboardButton(auction) for auction in buttons])
    for auction in getAuctions():
        bot.send_message(message.chat.id, auction, reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Повернутися до аукціонів')
def to_start(message):
    start(message)


@bot.message_handler(func=lambda message: message.text in getAuctions())
def choose_category(message):
    bot.send_message(message.chat.id, 'Чудово! На аукціоні представлені наступні роботи:')
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Повернутися до аукціонів')
    for work in getWorks(message.text):
        bot.send_message(message.chat.id, work)
        markup.add(work)
    if message.chat.id == 54778971:
        markup.add('Додати роботу')
        msg = bot.send_message(message.chat.id, 'Додати?', reply_markup=markup)
        bot.register_next_step_handler(msg, add_art_1, message.text)
    else:
        msg = bot.send_message(message.chat.id, 'Яка робота вас цікавить?', reply_markup=markup)
        bot.register_next_step_handler(msg, trade_1, message.text)


def trade_1(message, auction):
    if message.text == 'Повернутися до аукціонів':
        start(message)
    else:
        art = dict(db.child('auctions').child(auction).child('art').child(message.text).get().val())
        bot.send_message(message.chat.id, art['name'])
        bot.send_photo(message.chat.id, art['pic_url'])
        try:
            highest_bid = art['bids']['start_bid']
            highest_bidder_id = 0
        except Exception as e:
            print(e)
        try:
            for bid in art['bids']:
                if art['bids'][bid]['value'] > highest_bid['value']:
                    highest_bid = art['bids'][bid]
                    highest_bidder_id = art['bids'][bid]['id']
        except Exception as e:
            print(e)
        bot.send_message(message.chat.id, 'Поточна ставка ' + str(highest_bid['value']) + ' грн')
        if message.chat.id == highest_bidder_id:
            bot.send_message(message.chat.id, 'І це ваша ставка')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        bt1 = types.KeyboardButton('Зробити ставку')
        markup.add(bt1)
        markup.add('Повернутися до аукціонів')
        msg = bot.send_message(message.chat.id,
                               'Бажаєте зробити ставку?',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, make_bid, auction, art, highest_bid, highest_bidder_id)


def make_bid(message, auction, art, highest_bid, highest_bidder_id):
    if message.text == 'Повернутися до аукціонів':
        start(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Повернутися до аукціонів')
        msg = bot.reply_to(message, 'За яку суму бажаєте купити цю роботу?', reply_markup=markup)
        bot.register_next_step_handler(msg, accept_bid, auction, art, highest_bid, highest_bidder_id)


def accept_bid(message, auction, art, highest_bid, highest_bidder_id):
    if message.text == 'Повернутися до аукціонів':
        start(message)
    else:
        try:
            if int(message.text) > int(highest_bid['value']):
                bot.send_message(message.chat.id, 'Ваша ставка прийнята. Після завершення аукціону ми повідомимо '
                                                  'вас про результати', reply_markup=types.ReplyKeyboardRemove())
                full_bid = {'id': message.chat.id, 'value': int(message.text)}
                db.child('auctions').child(auction).child('art').child(art['name']).child('bids').push(full_bid)
                if highest_bidder_id != 0:
                    bot.send_message(highest_bidder_id, 'Ваша ставка на акціоні ' + auction + ' на роботу ' + art['name'] + ' була перебита')
                    bot.send_message(highest_bidder_id, 'Нова ставка - ' + message.text + ' грн')
                    bot.send_message(highest_bidder_id, 'Якщо бажаєте поборотись за цю роботу, оновіть вашу ставку!')
                time.sleep(2)
                start(message)
            else:
                bot.send_message(message.chat.id, 'Ваша ставка менша за поточну максимальну',
                                 reply_markup=types.ReplyKeyboardRemove())
                make_bid(message, auction, art, highest_bid, highest_bidder_id)
        except Exception as e:
            print('Something wrong with your bet', e)
            bot.send_message(message.chat.id, 'Ставка не прийнята. Використовуйте лише цифри')
            make_bid(message, auction, art, highest_bid, highest_bidder_id)

@bot.message_handler(func=lambda message: message.text == 'Створити аукціон')
def add_auction(message):
    msg = bot.reply_to(message, 'Введіть назву аукціону', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, add_date)


def add_date(message):
    auction = {'name': message.text}
    msg = bot.reply_to(message, 'Введіть дату початку аукціону у форматі DD:MM:YYYY')
    bot.register_next_step_handler(msg, add_date_end, auction)


def add_date_end(message, auction):
    auction['date_of_start'] = message.text
    msg = bot.reply_to(message, 'Введіть дату кінця аукціону у форматі DD:MM:YYYY')
    bot.register_next_step_handler(msg, add_art, auction)


def add_art(message, auction):
    auction['date_of_end'] = message.text
    try:
        db.child("auctions").child(auction['name']).set(auction)
    except Exception as ex:
        bot.send_message(message.chat.id, 'Сталась помилка створення аукціону')
        print(ex)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.chat.id, 'Зараз на аукціоні представлені наступні роботи:')
    try:
        auctionID = get_auction_by_name(auction['name'])
        for work in getWorks(auctionID):
            bot.send_message(message.chat.id, work)

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        bt1 = types.KeyboardButton('Додати роботу')
        markup.add(bt1)
        msg = bot.send_message(message.chat.id,
                               'Додати?',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, add_art_1, auctionID)

    except Exception as ex:
        bot.send_message(message.chat.id, 'Сталась помилка з пошуком аукціону')
        print(ex)


def add_art_1(message, auctionID):
    msg = bot.reply_to(message, 'Введіть назву та короткий опис роботи')
    bot.register_next_step_handler(msg, add_art_2, auctionID)


def add_art_2(message, auctionID):
    art = {'name': message.text}
    msg = bot.reply_to(message, 'Введіть стартову ціну в гривнях')
    bot.register_next_step_handler(msg, add_art_3, auctionID, art)


def add_art_3(message, auctionID, art):
    art['bids'] = {}
    art['bids']['start_bid'] = {}
    art['bids']['start_bid']['value'] = message.text
    art['bids']['start_bid']['id'] = 0
    msg = bot.reply_to(message, 'Введіть посилання на зображення')
    bot.register_next_step_handler(msg, add_art_4, auctionID, art)


def add_art_4(message, auctionID, art):
    art['pic_url'] = message.text
    try:
        db.child('auctions').child(auctionID).child('art').child(art['name']).set(art)
    except Exception as ex:
        bot.send_message(message.chat.id, 'Сталась помилка додавання роботи')
        print(ex)
    bot.send_message(message.chat.id, 'Роботу додано')
    bot.send_message(message.chat.id, art['name'])
    bot.send_message(message.chat.id, 'Стартова ціна: ' + art['bids']['0']['value'])
    bot.send_photo(message.chat.id, art['pic_url'])
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    bt1 = types.KeyboardButton('Додати роботу')
    markup.add(bt1)
    msg = bot.send_message(message.chat.id, 'Додати ще одну роботу?', reply_markup=markup)
    bot.register_next_step_handler(msg, add_art_1, auctionID)


# @bot.message_handler(func=lambda message: message.text == 'Додати роботу')
# def start(message):


@bot.message_handler(content_types=['sticker'])
def sticker(message):
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAALZ917FJNkYobdgo2LmDSaCE9eRX6kPAAKBYQAC4KOCB-bq_OmAUqhDGQQ')
    pass


bot.polling()
