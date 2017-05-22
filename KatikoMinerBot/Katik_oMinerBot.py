import config
import draw
import os
import telebot
import exceptions
import constants
import numpy as np

bot = telebot.TeleBot(config.token)
users = {}


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

    def init_game_field(self, user_arguments, chat_id):
        self.playing = True
        self.bomb_field = np.zeros((user_arguments.height, user_arguments.width))
        self.game_field = np.zeros((user_arguments.height, user_arguments.width))
        self.user_field = np.array([constants.EMPTY] * (user_arguments.width * user_arguments.height))
        self.user_field = np.resize(self.user_field, (user_arguments.height, user_arguments.width))
        self.height = user_arguments.height
        self.width = user_arguments.width
        self.bombs = user_arguments.bombs
        self.opened_cells = 0
        self.plant_bombs_()
        self.init_bomb_field_()
        self.won = False
        self.lost = False
        self.picture.new_field('{}.jpg'.format(chat_id), user_arguments.height, user_arguments.width)

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
                if 0 <= index_j + j < self.width and 0 <= index_i + i < self.height:
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
            self.user_field[x][y] = constants.EMPTY
        if self.bomb_field[x][y] == 1:
            self.lost = True
            self.draw_lose_field(x, y)
            self.playing = False
            return constants.LOSER
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
            return constants.WINNER
        else:
            return constants.INPROGRESS

    def open_zero_cells(self, x, y):
        if self.user_field[x][y] != constants.EMPTY:
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
        if self.user_field[x][y] == constants.FLAGGED:
            return False
        self.user_field[x][y] = constants.FLAGGED
        self.picture.draw_flag(x, y)
        return True

    def remove_flag_cell(self, x, y):
        if self.user_field[x][y] == constants.FLAGGED:
            self.user_field[x][y] = constants.EMPTY
            self.picture.remove_flag(x, y)
            return True
        return False

    def __str__(self):
        return str(self.user_field)


class FieldParams:
    def __init__(self, message_text):
        splited_message = message_text.split(' ')
        if len(splited_message) != 4 and len(splited_message) != 3:
            raise exceptions.InputErrorException(Exception)
        else:
            try:
                self.width = int(splited_message[1])
            except ValueError:
                raise exceptions.InputErrorException(Exception)
            try:
                self.height = int(splited_message[2])
            except ValueError:
                raise exceptions.InputErrorException(Exception)
            if len(splited_message) == 4:
                try:
                    self.bombs = int(splited_message[3])
                except ValueError:
                    raise exceptions.InputErrorException(Exception)
            else:
                self.bombs = max(1, int(0.25 * self.height * self.width))
        
        if self.height <= 0 or self.width <= 0:
            raise exceptions.IncorrectParamsException(Exception)
        if self.bombs >= self.width * self.height:
            raise exceptions.TooManyBombsException(Exception)
        if self.height > 15 or self.width > 15:
            raise exceptions.TooLargeFieldException(Exception)
        if self.bombs <= 0:
            raise exceptions.NotEnoughBombsException(Exception)


def registration_check(message):
    if message.chat.id not in users.keys():
        bot.send_message(message.chat.id, 'Начните новую игру')
        return False
    if not users[message.chat.id].playing:
        bot.send_message(message.chat.id, 'Начните новую игру')
        return False
    return True


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_sticker(message.chat.id, data='CAADAgADCBMAAkKvaQABJS_tlanrZB8C')
    bot.send_message(message.chat.id, constants.HELP_MESSAGE)
    users[message.chat.id] = GameField()


@bot.message_handler(commands=['new'])
def new_game_check(message):
    if message.chat.id not in users.keys():
        users[message.chat.id] = GameField()
    try:
        user_arguments = FieldParams(message.text)
    except exceptions.InputErrorException:
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    except exceptions.TooManyBombsException:
        bot.send_message(message.chat.id, "Слишком много бомб")
        return
    except exceptions.TooLargeFieldException:
        bot.send_message(message.chat.id, "Слишком большое поле : размеры должны быть меньше 16")
        return
    except exceptions.IncorrectParamsException:
        bot.send_message(message.chat.id, "Некорректный размер поля")
        return
    except exceptions.NotEnoughBombsException:
        bot.send_message(message.chat.id, "Маловато бомб")
        return
    if user_arguments.bombs % 10 == 1 and user_arguments.bombs != 11:
        bot.send_message(message.chat.id, 'На поле {} бомба'.format(user_arguments.bombs))
    elif 2 <= user_arguments.bombs % 10 <= 4 and (user_arguments.bombs <= 10 or user_arguments.bombs >= 20):
        bot.send_message(message.chat.id, 'Ha поле {} бомбы'.format(user_arguments.bombs))
    else:
        bot.send_message(message.chat.id, 'Ha поле {} бомб'.format(user_arguments.bombs))
    users[message.chat.id].init_game_field(user_arguments, message.chat.id)
    with open('/'.join([os.getcwd(), 'users/{}.jpg'.format(message.chat.id)]), 'rb') as photo:
        bot.send_photo(message.chat.id, photo)


class ActionParams:
    def __init__(self, message_text, message_id):
        splited_message = message_text.split(' ')
        if len(splited_message) != 3:
            raise exceptions.InputErrorException(Exception)
        else:
            try:
                self.x = int(splited_message[1]) - 1
            except ValueError:
                raise exceptions.InputErrorException(Exception)
            try:
                self.y = int(splited_message[2]) - 1
            except ValueError:
                raise InputErrorException(Exception)
        if self.x < 0 or self.x >= users[message_id].height:
            raise exceptions.IncorrectParamsException(Exception)
        if self.y < 0 or self.y >= users[message_id].width:
            raise exceptions.IncorrectParamsException(Exception)


@bot.message_handler(commands=['open'])
def open_cell_check(message):
    if not registration_check(message):
        return
    try:
        open_params = ActionParams(message.text, message.chat.id)
    except (exceptions.InputErrorException, exceptions.IncorrectParamsException):
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if users[message.chat.id].user_field[open_params.x][open_params.y] == constants.FLAGGED:
        question_message_open_flagged(message.chat.id, open_params.x, open_params.y)
    elif users[message.chat.id].user_field[open_params.x][open_params.y] != constants.EMPTY:
        bot.send_message(message.chat.id, 'Ячейка уже открыта')
    else:
        open_cell(message.chat.id, open_params.x, open_params.y)


def open_cell(chat_id, x, y):
    result = users[chat_id].open_cell(x, y)
    with open('/'.join([os.getcwd(), 'users/{}.jpg'.format(chat_id)]), 'rb') as photo:
        if result == constants.LOSER:
            bot.send_message(chat_id, 'Бууум! Ты проиграл!')
            bot.send_photo(chat_id, photo)
            bot.send_sticker(chat_id, data='CAADAgAD7wADcqrmBE6HbRTJbkh-Ag')
            return
        elif result == constants.WINNER:
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
    try:
        flag_params = ActionParams(message.text, message.chat.id)
    except (exceptions.IncorrectParamsException, exceptions.InputErrorException):
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if users[message.chat.id].user_field[flag_params.x][flag_params.y] != constants.EMPTY:
        bot.send_message(message.chat.id, "Ячейка уже открыта")
        return
    if not users[message.chat.id].flag_cell(flag_params.x, flag_params.y):
        bot.send_message(message.chat.id, 'В этой ячейке уже есть флажок')
    else:
        with open('/'.join([os.getcwd(), 'users/{}.jpg'.format(message.chat.id)]), 'rb') as photo:
            bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['remove_flag'])
def remove_flag_cell(message):
    if not registration_check(message):
        return
    try:
        remove_params =  ActionParams(message.text, message.chat.id)
    except (exceptions.InputErrorExceptionm, exceptions.IncorrectParamsException):
        bot.send_message(message.chat.id, 'Ошибка ввода')
        return
    if not users[message.chat.id].remove_flag_cell(remove_params.x, remove_params.y):
        bot.send_message(message.chat.id, 'В этой ячейке нет флажка')
        return
    with open('/'.join([os.getcwd(), 'users/{}.jpg'.format(message.chat.id)]), 'rb') as photo:
        bot.send_photo(message.chat.id, photo)


@bot.message_handler(command='help')
def help_(message):
    bot.send_message(message.chat.id, constants.HELP_MESSAGE)


@bot.message_handler()
def wrong_command(message):
    bot.send_message(message.chat.id, 'Ошибка ввода')


if __name__ == '__main__':
    bot.polling(none_stop=False)


