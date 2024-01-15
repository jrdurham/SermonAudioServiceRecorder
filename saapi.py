import json
import os
import requests
import sermonaudio
from datetime import datetime, timedelta
import time
from sermonaudio.node.requests import Node
from sermonaudio.broadcaster.requests import Broadcaster
from sermonaudio import models
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

SA_API_KEY = os.getenv("SA_API_KEY")
sermonaudio.set_api_key(SA_API_KEY)

def message(message):
    print(f"[saapi] {message}")


def get_series_list():
    page = 1
    titles = []
    while True:
        response = Node.get_series_list(
            broadcaster_id="calvaryfaytn", page={page}, page_size=5
        )
        titles.extend([i.title for i in response.results])
        if response.next_url:
            page += 1
        else:
            break
    return titles


def create_sermon(
    full_title, speaker_name, publish_timestamp, preach_date, event_type, bible_text
):
    response = Broadcaster.create_or_update_sermon(
        full_title=full_title,
        speaker_name=speaker_name,
        publish_timestamp=datetime.now() + timedelta(minutes=5),
        preach_date=datetime.strptime(preach_date, "%Y%m%d"),
        event_type=models.SermonEventType(value=event_type),
        bible_text=bible_text,
        accept_copyright=True,
        sermon_id="",
        display_title="",
        subtitle="",
        more_info_text="",
        language_code="en",
        keywords=[],
    )
    if response.sermon_id:
        message(f"Sermon Creation Success. SermonID: {response.sermon_id}")
        return response.sermon_id
    else:
        message(f"[ERROR] Sermon Creation Failed.\nError:\n{response}")


def upload_audio(sermon_id, path):
    Broadcaster.upload_audio(sermon_id=sermon_id, path=path)
