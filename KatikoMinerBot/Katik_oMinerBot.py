import config
import draw
import telebot
import numpy as np
from telebot import types

bot = telebot.TeleBot(config.token)
N, M = 0, 0
Users = {}


class GameField:
    def __init__(self):
        self.playing = False
        self.bomb_field = np.array([])
        self.user_field = np.array([])
        self.game_field = np.array([])
        self.height = 0
        self.width = 0
        self.bombs = 0
        self.opened_cells = 0
        self.picture = draw.PicField()
        self.won = False
        self.lost = False

    def delete_data(self):
        self.playing = False
        self.bomb_field = np.array([])
        self.user_field = np.array([])
        self.game_field = np.array([])
        self.height = 0
        self.width = 0
        self.bombs = 0
        self.opened_cells = 0
        self.won = False
        self.lost = False

    def init_game_field(self, bomb_field_height, bomb_field_width, bombs_num, chat_id):
        self.playing = True
        self.bomb_field = np.zeros((bomb_field_height, bomb_field_width))
        self.game_field = np.zeros((bomb_field_height, bomb_field_width))
        self.user_field = np.array([-2] * (bomb_field_width * bomb_field_height))
        self.user_field = np.resize(self.user_field, (bomb_field_height, bomb_field_width))
        self.height = bomb_field_height
        self.width = bomb_field_width
        self.bombs = bombs_num
        self.opened_cells = 0
        self.plant_bombs_()
        self.init_bomb_field_()
        self.won = False
        self.lost = False
        self.picture.new_field('{}.jpg'.format(chat_id), bomb_field_height, bomb_field_width)

    def plant_bombs_(self):
        self.bomb_field = np.hstack(self.bomb_field)
        for i in range(0, self.bombs):
            self.bomb_field[i] = 1
        np.random.shuffle(self.bomb_field)
        self.bomb_field = np.resize(self.bomb_field, (self.height, self.width))

    def init_bomb_field_(self):
        print(self.bomb_field)
        for i in range(0, self.height):
            for j in range(0, self.width):
                self.game_field[i][j] = self.init_cell_(i, j)

    def init_cell_(self, index_i, index_j):
        if self.bomb_field[index_i][index_j] == 1:
            return 0
        sum_ = 0
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                if index_j + j >= 0 and index_j + j < self.width and index_i + i >= 0 and index_i + i < self.height:
                   sum_ += self.bomb_field[index_i + i][index_j + j]
        return sum_

    def draw_lose_field(self, x, y):
        for i in range(0, self.height):
            for j in range(0, self.width):
                if not(x == i and y == j) and self.bomb_field[i][j] == 1:
                    self.picture.draw_bomb(i, j)
        self.picture.draw_exploded_bomb(x, y)

    def draw_win_field(self):
        for i in range(0, self.height):
            for j in range(0, self.width):
                if self.bomb_field[i][j] == 1:
                    self.picture.draw_bomb(i, j)

    def open_cell(self, x, y):
        if self.user_field[x][y] == -1:
            self.user_field[x][y] = -2
        if self.bomb_field[x][y] == 1:
            self.lost = True
            self.draw_lose_field(x, y)
            self.playing = False
            return -1
        elif self.game_field[x][y] != 0:
            self.user_field[x][y] = self.game_field[x][y]
            self.picture.draw_number(x, y, self.user_field[x][y])
            self.opened_cells += 1
        else:
            self.open_zero_cells(x, y)
        if self.opened_cells == self.height * self.width - self.bombs:
            self.won = True
            self.draw_win_field()
            self.playing = False
            return 1
        else:
            return 0

    def open_zero_cells(self, x, y):
        if self.user_field[x][y] != -2:
            return
        self.user_field[x][y] = self.game_field[x][y]
        self.opened_cells += 1
        self.picture.draw_number(x, y, self.user_field[x][y])
        if self.game_field[x][y] != 0:
            return
        if x > 0:
            self.open_zero_cells(x - 1, y)
        if y > 0:
            self.open_zero_cells(x, y - 1)
        if x < self.height - 1:
            self.open_zero_cells(x + 1, y)
        if y < self.width - 1:
            self.open_zero_cells(x, y + 1)

    def flag_cell(self, x, y):
        if self.user_field[x][y] == -1:
            return False
        self.user_field[x][y] = -1
        self.picture.draw_flag(x, y)
        return True

    def remove_flag_cell(self, x, y):
        if self.user_field[x][y] == -1:
            self.user_field[x][y] = -2
            self.picture.remove_flag(x, y)
            return True
        return False

    def win_field(self):
        return str(self.user_field)

    def lose_field(self):
        return str(self.user_field)

    def __str__(self):
        return str(self.user_field)


def parse_command_new_game(message):
    splited_message = message.split(' ')
    if len(splited_message) != 4 and len(splited_message) != 3:
        return -1, -1, -1
    else:
            try:
                height = int(splited_message[1])
            except ValueError:
                return -1, -1, -1
            try:
                width = int(splited_message[2])
            except ValueError:
                return -1, -1, -1
            if len(splited_message) == 4:
                try:
                    bombs = int(splited_message[3])
                except ValueError:
                    return -1, - 1, -1
            else:
                bombs = max(1, int(0.25 * height * width))
    return height, width, bombs


def parse_command_open_flag(message, id):
    splited_message = message.split(' ')
    if len(splited_message) != 3:
        return -1, -1
    else:
        try:
            x = int(splited_message[1]) - 1
        except ValueError:
            return -1, -1
        try:
            y = int(splited_message[2]) - 1
        except ValueError:
            return -1, -1
    if x < 0 or x >= Users[id].height:
        return -1, -1
    if y < 0 or y >= Users[id].width:
        return -1, -1
    return x, y


def registration_check(message):
    if message.chat.id not in Users.keys():
        bot.send_message(message.chat.id, 'Начните новую игру')
        return False
    if not Users[message.chat.id].playing:
        bot.send_message(message.chat.id, 'Начните новую игру')
        return False
    return True


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, data='CAADAgADCBMAAkKvaQABJS_tlanrZB8C')
    bot.send_message(message.chat.id, 'Привет, ' + message.from_user.first_name + '!')
    Users[message.chat.id] = GameField()


@bot.message_handler(commands=['new'])
def new_game_check(message):
    if message.chat.id not in Users.keys():
        Users[message.chat.id] = GameField()
    bomb_field_height, bomb_field_width, bombs_num = parse_command_new_game(message.text)
    bomb_field_height, bomb_field_width = bomb_field_width, bomb_field_height
    if bomb_field_height == -1:
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if bombs_num >= bomb_field_width * bomb_field_height:
        bot.send_message(message.chat.id, "Слишком много бомб")
        return
    if bomb_field_height > 15 or bomb_field_width > 15:
        bot.send_message(message.chat.id, "Слишком большое поле : размеры должны быть меньше 16")
        return
    if bomb_field_height <= 0 or bomb_field_width <= 0:
        bot.send_message(message.chat.id, "Некорректный размер поля")
        return
    if bombs_num <= 0:
        bot.send_message(message.chat.id, "Маловато бомб")
        return
    if bombs_num % 10 == 1 and bombs_num != 11:
        bot.send_message(message.chat.id, 'На поле {} бомба'.format(bombs_num))
    elif bombs_num % 10 >= 2 and bombs_num % 10 <= 4 and (bombs_num <= 10 or bombs_num >= 20):
        bot.send_message(message.chat.id, 'Ha поле {} бомбы'.format(bombs_num))
    else:
        bot.send_message(message.chat.id, 'Ha поле {} бомб'.format(bombs_num))
    Users[message.chat.id].init_game_field(bomb_field_width, bomb_field_height, bombs_num, message.chat.id)
    photo = open('users/{}.jpg'.format(message.chat.id), 'rb')
    bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['open'])
def open_cell_check(message):
    if not registration_check(message):
        return
    x, y = parse_command_open_flag(message.text, message.chat.id)
    if x == -1 or y == -1:
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if Users[message.chat.id].user_field[x][y] == -1:
        question_message_open_flagged(message.chat.id, x, y)
    elif Users[message.chat.id].user_field[x][y] != -2:
        bot.send_message(message.chat.id, 'Ячейка уже открыта')
    else:
        open_cell(message.chat.id, x, y)


def open_cell(chat_id, x, y):
    result = Users[chat_id].open_cell(x, y)
    photo = open('users/{}.jpg'.format(chat_id), 'rb')
    if result == -1:
        bot.send_message(chat_id, 'Бууум! Ты проиграл!')
        bot.send_photo(chat_id, photo)
        bot.send_sticker(chat_id, data='CAADAgAD7wADcqrmBE6HbRTJbkh-Ag')
        return
    elif result == 1:
        bot.send_message(chat_id, 'С победой!')
        bot.send_photo(chat_id, photo)
        bot.send_sticker(chat_id, data='CAADAgADBwQAAnKq5gTVZI_e9jff8wI')
        return
    bot.send_photo(chat_id, photo)


def question_message_open_flagged(chat_id, x, y):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*[types.InlineKeyboardButton(text=ans, callback_data=' '.join([ans,
                                                                                str(x), str(y)])) for ans in ['Да',
                                                                                                              'Нет']])
    bot.send_message(chat_id, 'Вы уверены, что хотите открыть ячейку с флажком?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda ans: True)
def inline(ans):
    ans_arg = ans.data.split(' ')
    if ans_arg[0] == 'Да':
        bot.edit_message_text(chat_id=ans.message.chat.id, message_id=ans.message.message_id,
                              text='Ну, смотри, друг')
        open_cell(ans.message.chat.id, int(ans_arg[1]), int(ans_arg[2]))
    else:
        bot.edit_message_text(chat_id=ans.message.chat.id, message_id=ans.message.message_id,
                              text='Будь внимательнее, друг, повсюду мины')


@bot.message_handler(commands=['flag'])
def flag_cell(message):
    if not registration_check(message):
        return
    x, y = parse_command_open_flag(message.text, message.chat.id)
    if x == -1 or y == -1:
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if Users[message.chat.id].user_field[x][y] != -2:
        bot.send_message(message.chat.id, "Ячейка уже открыта")
        return
    if not Users[message.chat.id].flag_cell(x, y):
        bot.send_message(message.chat.id, 'В этой ячейке уже есть флажок')
    else:
        photo = open('users/{}.jpg'.format(message.chat.id), 'rb')
        bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['remove_flag'])
def remove_flag_cell(message):
    if not registration_check(message):
        return
    x, y = parse_command_open_flag(message.text, message.chat.id)
    if x == -1 or y == -1:
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if not Users[message.chat.id].remove_flag_cell(x, y):
        bot.send_message(message.chat.id, 'В этой ячейке нет флажка')
        return
    photo = open('users/{}.jpg'.format(message.chat.id), 'rb')
    bot.send_photo(message.chat.id, photo)


@bot.message_handler(content_types=['sticker'])
def wrong_command(message):
    bot.send_message(message.chat.id, 'Ошибка ввода')


if __name__ == '__main__':
    bot.polling(none_stop=False)


