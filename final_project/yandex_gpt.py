import requests
import logging
import requests
from config import MAX_GPT_TOKENS, SYSTEM_PROMPT, GPT_URL, GPT_MODEL, URL
from creds import get_creds
IAM_TOKEN, FOLDER_ID = get_creds()


def count_gpt_tokens(messages):
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "messages": messages
    }
    try:
        response = requests.post(url=GPT_URL, json=data, headers=headers).json()['tokens']
        return len(response)
    except Exception as e:
        logging.error(e)
        return 0


def ask_gpt(messages):
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f"gpt://{FOLDER_ID}/{GPT_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": MAX_GPT_TOKENS
        },
        "messages": SYSTEM_PROMPT + messages
    }
    try:
        response = requests.post(GPT_URL, headers=headers, json=data)
        if response.status_code != 200:
            return False, f"Ошибка {response.status_code}", None
        answer = response.json()['result']['alternatives'][0]['message']['text']
        tokens_in_answer = count_gpt_tokens([{'role': 'assistant', 'text': answer}])
        return True, answer, tokens_in_answer
    except Exception as e:
        logging.error(e)
        return False, "Ошибка при обращении к GPT",  None


def ask_speech_kit_tts(user: dict, text: str):
    url = URL
    headers = {'Authorization': f'Bearer {IAM_TOKEN}'}
    data = {'text': text,
            'lang': 'ru-RU',
            'voice': 'ermil',
            'emotion': 'good',
            'folderId': FOLDER_ID,
            }

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return True, response.content
        else:
            return False, "Ошибка при запросе в SpeechKit"
    except Exception as e:
        result = f"Error '{e}' while requesting SpeechKit"

    return result


# stt
def ask_speech_kit_stt(user: dict, data):
    params = "&".join([
        "topic=general",
        f"folderId={FOLDER_ID}",
        "lang=ru-RU"
    ])
    url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}"
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        decoded_data = response.json()
        if decoded_data.get("error_code") is None:
            return True, decoded_data.get(
                "result")
        else:
            return False, "Ошибка при запросе в SpeechKit"
    except Exception as e:
        result = f"Error '{e}' while requesting SpeechKit"

    return result


if __name__ == '__main__':
    print(count_gpt_tokens([{'role': 'user', 'text': 'Привет'}]))

