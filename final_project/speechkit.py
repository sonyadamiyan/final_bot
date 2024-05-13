import requests
import logging
from config import LANGUAGE, VOICE, SPEECHKIT_MODEL, URL, LOGS, URL_STT, URL_TTS
from creds import get_creds

IAM_TOKEN, FOLDER_ID = get_creds()
logging.basicConfig(filename=LOGS, level=logging.ERROR,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")


def text_to_speech(text):
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}"}
    data = {
        "text": text,
        "lang": LANGUAGE,
        "voice": VOICE,
        "folderId": FOLDER_ID}
    response = requests.post(URL_TTS, headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content
    else:
        return False, logging.debug("При запросе в SpeechKit возникла ошибка")


def speech_to_text(data):
    params = "&".join([
        f"topic={SPEECHKIT_MODEL}",
        f"folderId={FOLDER_ID}",
        f"lang={LANGUAGE}"
    ])
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}"}
    response = requests.post(URL_STT + params, headers=headers, data=data)
    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")
    else:
        return False, logging.debug("При запросе в SpeechKit возникла ошибка")

