
import telebot


class telegram:
    def __init__(self):
        self.bot = telebot.TeleBot(
            "xxxxxxxxx:your_bot_token")
        self.chat_id = [youtelegramid]

    def send_message(self, item):
        button = telebot.types.InlineKeyboardButton(
            text='Open Keepa', url='https://keepa.com/#!product/9-'+str(item['asin']))

        keyboard = telebot.types.InlineKeyboardMarkup()

        keyboard.add(button)
        message_text = "🎉🎉🎉 NEW DISCOUNT 🎉🎉🎉\n"
        message_text += '\nPrice: ' + \
            str(item['price'])+'🔥 Discount: '+str(item['discount'])+'%🔥'
        message_text += 'https://www.amazon.' + \
            str(item['domain'])+'/dp/'+str(item['asin'])

        for i in self.chat_id:
            self.bot.send_message(i, message_text, reply_markup=keyboard)
