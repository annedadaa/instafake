# -*- coding: utf-8 -*-
import telebot  # импортируем модуль pyTelegramBotAPI
import conf     # импортируем наш секретный токен
import re
import pandas as pd
import hashlib
import string
import random
# from instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
import datetime
from instagram_private_api import Client, ClientCompatPatch
from joblib import dump, load
import urllib.parse


# функция для выдачи инфы по профилю
api = Client(conf.uname, conf.pw)
from instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
# без этого куска кода ничего не работает
# https://github.com/ping/instagram_private_api/issues/170


class MyClient(Client):

    @staticmethod
    def _extract_rhx_gis(html):
        options = string.ascii_lowercase + string.digits
        text = ''.join([random.choice(options) for _ in range(8)])
        return hashlib.md5(text.encode()).hexdigest()

    def login(self):
        """Login to the web site."""
        if not self.username or not self.password:
            raise ClientError('username/password is blank')

        time = str(int(datetime.datetime.now().timestamp()))
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{time}:{self.password}"

        params = {'username': self.username, 'enc_password': enc_password, 'queryParams': '{}', 'optIntoOneTap': False}
        self._init_rollout_hash()
        login_res = self._make_request('https://www.instagram.com/accounts/login/ajax/', params=params)
        if not login_res.get('status', '') == 'ok' or not login_res.get ('authenticated'):
            raise ClientLoginError('Unable to login')

        if self.on_login:
            on_login_callback = self.on_login
            on_login_callback(self)
        return login_res


client = MyClient(auto_patch=True, authenticate=True, username=conf.uname, password=conf.pw)


def get_info(name_of_user):
    profile_pic = []
    full_name = []
    username = []
    bio = []
    external_url = []
    posts = []
    followers = []
    private = []
    username_num = []
    full_name_num = []
    user = []
    follows = []
    try:
        full_text = client.user_info2(name_of_user)
        prof_pic = full_text['profile_pic_url']
        if prof_pic == 'https://instagram.fesb6-1.fna.fbcdn.net/v/t51.2885-19/44884218_345707102882519_2446069589734326272_n.jpg?_nc_ht=instagram.fesb6-1.fna.fbcdn.net&_nc_ohc=XFLgsavKWt0AX_lEXQh&edm=AJ9x6zYBAAAA&ccb=7-4&oh=5a7a793e1b0b23e7108d5a8ffda95511&oe=60DA820F&_nc_sid=cff2a4&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.2-ccb7-4':
            profile_pic.append(0)
        else:
            profile_pic.append(1)
        bio.append(len(full_text['biography']))
        priv = full_text['is_private']
        if priv == 'False':
            private.append(1)
        else:
            private.append(0)
        usern = full_text['username']
        numbers = len(re.sub("[^0-9]", "", usern))
        username_num.append((numbers/len(usern)))
        full_n = full_text['full_name']
        full_name.append(len(full_n.split(' ')))
        if usern == full_n:
            username.append(1)
        else:
            username.append(0)
        full_n_num = len(re.sub("[^0-9]", "", full_n))
        if len(full_n) >0:
            full_name_num.append(full_n_num/len(full_n))
        else:
            full_name_num.append(0)
        followers.append(full_text['edge_followed_by']['count'])
        follows.append(full_text['edge_follow']['count'])
        posts.append(full_text['edge_owner_to_timeline_media']['count'])
        url = full_text['external_url']
        if url is not None:
            external_url.append(0)
        else:
            external_url.append(0)
        user.append(usern)
        df_dict = {'profile_pic': profile_pic, 'nums/length username': username_num,
                   'fullname words': full_name, 'nums/length fullname': full_name_num,
                   'name==username': username, 'description': bio, 'external URL': external_url,
                   'private': private, '#posts': posts, '#followers': followers, '#follows': follows}
        df = pd.DataFrame(df_dict)
        return df
    except ClientError:
        return 'None'


model = load('filename-5.joblib')

# telebot.apihelper.proxy = conf.PROXY
bot = telebot.TeleBot(conf.TOKEN)  # создаем бота

# этот обработчик запускает функцию send_welcome, когда пользователь отправляет команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Введи юзернейм пользователя инстаграма."  # приветствие и краткая инструкция по запросу
    )


@bot.message_handler(func=lambda m: True)  # обработка введенного сообщения
def send_username(message):
    message.text = urllib.parse.quote(message.text)
    info = get_info(message.text)
    if not isinstance(info, str):
        y = model.predict(info)
        if y[0] == 1:
            for probs, pred in zip(model.predict_proba(info), model.predict(info)):
                if round(probs[pred], 3) == 1:
                    bot.send_message(chat_id=message.chat.id, text=message.text + ' точно фейковый аккаунт :(')
                else:
                    bot.send_message(chat_id=message.chat.id, text='с вероятностью ' + str(round(probs[pred], 3)) + ' '
                                                                   + message.text + ' - фейковый аккаунт :(')
        else:
            for probs, pred in zip(model.predict_proba(info), model.predict(info)):
                if round(probs[pred], 3) == 1:
                    bot.send_message(chat_id=message.chat.id, text=message.text + ' точно реальный аккаунт :)')
                else:
                    bot.send_message(chat_id=message.chat.id, text='с вероятностью ' + str(round(probs[pred], 3)) + ' '
                                                                   + message.text + ' - реальный аккаунт :)')
    else:
        bot.send_message(chat_id=message.chat.id, text='такого аккаунта нет! попробуй ввести снова.')


if __name__ == '__main__':  # запуск бота
    bot.polling(none_stop=True)
