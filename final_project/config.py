LANGUAGE = "ru-RU"
SPEECHKIT_MODEL = "general"
VOICE = "ermil"
HOME_DIR = '/Users/shuva/pythonProject2/pythonProject11/final_project'
LOGS = f'{HOME_DIR}/logs.txt'
DB_FILE = f'{HOME_DIR}/messages.db'

IAM_TOKEN_PATH = f'{HOME_DIR}/creds/iam_token.txt'
FOLDER_ID_PATH = f'{HOME_DIR}/creds/folder_id.txt'
BOT_TOKEN_PATH = f'{HOME_DIR}/creds/bot_token.txt'

MAX_USERS = 2
MAX_GPT_TOKENS = 100
COUNT_LAST_MSG = 3

MAX_USER_STT_BLOCKS = 10
MAX_USER_TTS_SYMBOLS = 100_000
MAX_USER_GPT_TOKENS = 5_000

MAX_USER_SYMBOLS = 2000
MAX_USER_BLOCKS = 15

URL = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
GPT_MODEL = "yandexgpt-lite"

SYSTEM_PROMPT = [{"role": "system", "text": "Ты веселый собеседник."
                                            "Чётко и понятно отвечай на все вопросы и не говори ничего лишнего"
                                            "Не объясняй пользователю, что ты умеешь и можешь."
                                            "Изображай человека"}]


