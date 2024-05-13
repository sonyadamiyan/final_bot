import sqlite3
import logging
from config import DB_FILE, MAX_USER_BLOCKS, MAX_USER_SYMBOLS, LOGS
path_to_db = DB_FILE

logging.basicConfig(filename=LOGS, level=logging.ERROR,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")


def create_database():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                role TEXT,
                total_gpt_tokens INTEGER,
                tts_symbols INTEGER,
                stt_blocks INTEGER)
            ''')

            # tts
            logging.info("DATABASE: База данных создана")
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS TTS ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'user_id INTEGER, '
                'content TEXT, '
                'symbols INT'
                ')'
            )

            # таблицa stt
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS STT ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'user_id INTEGER, '
                'filename TEXT, '
                'content TEXT, '
                'blocks INT'
                ')'
            )
    except Exception as e:
        logging.debug(e)
        return None


def add_message(user_id, full_message):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            message, role, total_gpt_tokens, tts_symbols, stt_blocks = full_message
            cursor.execute('''
                    INSERT INTO messages (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                           (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks)
                           )
            conn.commit()
            logging.info(f"DATABASE: INSERT INTO messages "
                         f"VALUES ({user_id}, {message}, {role}, {total_gpt_tokens}, {tts_symbols}, {stt_blocks})")
    except Exception as e:
        logging.debug(e)
        return None


def count_users(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT COUNT(DISTINCT user_id) FROM messages WHERE user_id <> ?''', (user_id,))
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        logging.debug(e)
        return None



def select_n_last_messages(user_id, n_last_messages=4):
    messages = []
    total_spent_tokens = 0
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT message, role, total_gpt_tokens FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?''',
                           (user_id, n_last_messages))
            data = cursor.fetchall()
            if data and data[0]:
                for message in reversed(data):
                    messages.append({'text': message[0], 'role': message[1]})
                    total_spent_tokens = max(total_spent_tokens, message[2])
            return messages, total_spent_tokens
    except Exception as e:
        logging.debug(e)
        return messages, total_spent_tokens


def count_all_limits(user_id, limit_type):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''SELECT SUM({limit_type}) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            if data and data[0]:
                logging.info(f"DATABASE: У user_id={user_id} использовано {data[0]} {limit_type}")
                return data[0]
            else:
                return 0
    except Exception as e:
        logging.debug(e)
        return 0


# потраченные токены
def user_tokens(db_connection, user) -> int:
    cursor = db_connection.cursor()
    query = ('SELECT sum(symbols) FROM TTS '
             'WHERE user_id = ?;')
    try:
        cursor.execute(query, (user['user_id'],))
        res = cursor.fetchone()
        if res[0] is None:
            return 0
        else:
            return res[0]
    except Exception as e:
        return 0


# tts
def tts_init(db_connection, user, content, symbols):
    cursor = db_connection.cursor()
    data = (
        user['user_id'],
        content,
        symbols
    )
    try:
        cursor.execute('INSERT INTO TTS '
                       '(user_id, content, symbols) '
                       'VALUES (?, ?, ?);',
                       data)
        db_connection.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return False


# лимит на символы для tts
def limit_symbols(db_connection, user_id):
    return user_tokens(db_connection, user_id) >= MAX_USER_SYMBOLS


# лимит для stt
def is_limit_blocks(db_connection, user_id):
    return user_blocks(db_connection, user_id) >= MAX_USER_BLOCKS


# stt
def user_blocks(db_connection, user) -> int:
    cursor = db_connection.cursor()
    query = ('SELECT sum(blocks) FROM STT '
             'WHERE user_id = ?;')
    try:
        cursor.execute(query, (user['user_id'],))
        res = cursor.fetchone()
        if res[0] is None:
            print(f"get_user_blocks None = 0")
            return 0
        else:
            print(f"get_user_blocks {res[0]}")
            return res[0]
    except Exception as e:
        return 0


def insert_stt(db_connection, user, filename, content, blocks):
    cursor = db_connection.cursor()
    data = (
        user['user_id'],
        filename,
        content,
        blocks
    )
    try:
        cursor.execute('INSERT INTO STT '
                       '(user_id, filename, content, blocks) '
                       'VALUES (?, ?, ?, ?);',
                       data)
        db_connection.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return False

