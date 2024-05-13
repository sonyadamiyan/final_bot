import telebot
import math
import logging
from telebot.types import ReplyKeyboardMarkup, Message, BotCommand, BotCommandScope
from validators import check_number_of_users, is_gpt_token_limit, is_stt_block_limit, is_tts_symbol_limit
from yandex_gpt import ask_gpt, ask_speech_kit_stt, ask_speech_kit_tts
from config import COUNT_LAST_MSG, LOGS
from database import create_database, add_message, select_n_last_messages, insert_stt, is_limit_blocks, limit_symbols, tts_init
from speechkit import text_to_speech, speech_to_text
from creds import get_bot_token

bot = telebot.TeleBot(get_bot_token())
user_data = {}
db_file = "databse.db"


# кнопки ответа
def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(
        row_width=1,
        resize_keyboard=True
    )
    keyboard.add(*buttons_list)
    return keyboard


def register_comands(message):
    commands = [  # Установка списка команд с областью видимости и описанием
        BotCommand("start", "запуск бота"),
        BotCommand("tts", "озвучить текст"),
        BotCommand("stt", "перевести голосовое сообщение в текст")]
    bot.set_my_commands(commands)
    BotCommandScope('private', chat_id=message.chat.id)


def user(mes):
    global user_data, db_db
    user_id = mes.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
        user_data[user_id]['user_id'] = user_id


@bot.message_handler(commands=["start"])
def send_welcome(message):
    logging.info("бот запущен")
    bot.reply_to(message,
                 text="Привет!\n"
                        "Я могу ответить на любой твой вопрос или просто поболтать\n"
                        "Присылаю ответ в том же формате, в котором ты присылал запрос:\n"
                        "(текст в ответ на текст, голос в ответ на голос)")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    try:
        user_id = message.from_user.id
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return
        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)
        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(message.from_user.id, "Ошибка. попробуй задать вопрос еще раз")


@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return
        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)
        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)

    except Exception as e:
        logging.error(e)
        user_id = message.from_user.id
        bot.send_message(user_id, "Ошибка. попробуй задать вопрос еще раз")


@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.from_user.id, "Ошибка. я отвечаю только на текстовое или голосовое сообщение")


@bot.message_handler(commands=['tts'])
def handle_tts(mes: Message):
    global db_db, user_data
    user_id = mes.from_user.id
    user(mes)
    bot.send_message(user_id,
                     text="Напиши текст,который хочешь озвучить\n"
                          "на русском или анлийском языках")
    bot.register_next_step_handler(mes, start_tts)


def start_tts(mes: Message):
    global db_db, user_data
    user_id = mes.from_user.id
    user(mes)
    text_symbols = len(mes.text)
    if text_symbols > 150:
        bot.send_message(
            user_id,
            text="Cлишком длинный текст, нужно его сократить до 150 символов")
        return
    elif limit_symbols(db_db, user_data[user_id]):
        bot.send_message(
            user_id,
            text="Превышен лимит символов",)
        return

    success, response = ask_speech_kit_tts(user_data[user_id], mes.text)
    if success:
        tts_init(db_db, user_data[user_id], mes.text, text_symbols)
        with open(f"tts{user_id}.ogg", "wb") as f:
            f.write(response)
        with open(f"tts{user_id}.ogg", "rb") as f:
            bot.send_audio(user_id, f)
            f.close()
    else:
        bot.send_message(
            user_id,
            text="Ошибка :( \n"
            f"{response}",)


# stt
@bot.message_handler(commands=['stt'])
def handle_stt(mes: Message):
    global db_db, user_data
    user_id = mes.from_user.id
    user(mes)
    bot.send_message(user_id,
                     text='Запиши голосовое сообщение, которое хочешь превратить в текст')
    bot.register_next_step_handler(mes, start_stt)


def start_stt(mes: Message):
    global db_db, user_data
    user_id = mes.from_user.id
    user(mes)
    # ограничение по времени и сообщ только гс
    if not mes.voice:
        bot.send_message(
            user_id,
            f'Ошибка\n'
            f'Отправь голосовое сообщение')
        return
    elif mes.voice.duration > 15:
        bot.send_message(
            user_id,
            text='Cлишком длинное сообщение\n'
            'Сократи его до 15 сокунд!')
        return

    elif is_limit_blocks(db_db, user_data[user_id]):
        bot.send_message(
            user_id,
            text="Превышен лимит",)
        return
    else:
        file_id = mes.voice.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        stt_blocks = math.ceil(mes.voice.duration / 15)
        try:
            with open(file_info.file_path, 'wb') as stt_file:
                stt_file.write(downloaded_file)
        except Exception as e:
            logging.error(f"{e}")
        try:
            with open(file_info.file_path, "rb") as stt_file:
                downloaded_file2 = stt_file.read()
        except Exception as e:
            logging.error(f"{e}")
        success, res = ask_speech_kit_stt(user_data[user_id], downloaded_file)
        if success:
            bot.send_message(
                user_id,
                f'Твоё сообщение:\n'
                f'{res}\n\n'
                f'Если хочешь попробывать еще /stt')
        else:
            bot.send_message(
                user_id,
                f'Не удалось распознать речь')
        insert_stt(db_db, user_data[user_id],
                   file_info.file_path, content=res, blocks=stt_blocks)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H",
        filename=LOGS,
        filemode="w",
        encoding='utf-8',
        force=True)
    db_db = create_database()
    create_database()
    bot.infinity_polling()
    logging.info("Бот запущен")
