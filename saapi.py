from datetime import datetime, timedelta

import requests
import sermonaudio
from sermonaudio import models
from sermonaudio.broadcaster.requests import Broadcaster
from sermonaudio.node.requests import Node

from sasrconfig import config


def message(saae, info):
    saae.sar.write_console(f"[API] {info}")
    print(f"[saAudioEngine] {info}")


def check_broadcaster():
    sa_api_key = str(config()["SA_API_KEY"])
    if "BROADCASTER_ID" in config() and len(str(config()["BROADCASTER_ID"])) > 0:
        broadcaster_id = str(config()["BROADCASTER_ID"])
        url = f"https://api.sermonaudio.com/v2/node/broadcasters/{broadcaster_id}?lite=true"
        headers = {"accept": "application/json", "X-Api-Key": f"{sa_api_key}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    else:
        return False


def check_key():
    if "SA_API_KEY" in config() and len(str(config()["SA_API_KEY"])) == 36:
        broadcaster_id = str(config()["BROADCASTER_ID"])
        sa_api_key = str(config()["SA_API_KEY"])
        try:
            sermon_id = (
                Node.get_sermons(
                    broadcaster_id=f"{broadcaster_id}", page=1, page_size=1
                )
                .results[0]
                .sermon_id
            )
        except sermonaudio.node.requests.NodeAPIError:
            return str("bad-id")
        except IndexError:
            return str("bad-id")
        url = f"https://api.sermonaudio.com/v2/node/sermons/{sermon_id}"

        headers = {
            "accept": "*/*",
            "X-API-Key": f"{sa_api_key}",
            "Content-Type": "application/json",
        }

        response = requests.patch(url, headers=headers)
        if response.status_code == 422:
            return str("valid")
        elif response.status_code == 401 or 404:
            return str("invalid")
        else:
            return str("invalid")
    else:
        return "no-key"


def get_series_titles():
    broadcaster_id = str(config()["BROADCASTER_ID"])
    sa_api_key = str(config()["SA_API_KEY"])
    sermonaudio.set_api_key(f"{sa_api_key}")
    page = 1
    titles = []
    if check_broadcaster():
        while True:
            response = Node.get_series_list(
                broadcaster_id=f"{broadcaster_id}", page=page, page_size=5
            )
            titles.extend([i.title for i in response.results])
            if response.next_url:
                page += 1
            else:
                break
        return titles
    else:
        return ["Enter Member ID in Settings."]


def get_series_id(series_name):
    broadcaster_id = str(config()["BROADCASTER_ID"])
    sa_api_key = str(config()["SA_API_KEY"])
    sermonaudio.set_api_key(f"{sa_api_key}")
    page = 1
    while True:
        response = Node.get_series_list(
            broadcaster_id=f"{broadcaster_id}", page=page, page_size=5
        )
        for series in response.results:
            if series.title == f"{series_name}":
                return series.series_id
        if response.next_url:
            page += 1
        else:
            return False


def create_sermon(
    saae, full_title, speaker_name, preach_date, event_type, bible_text, series=None
):
    broadcaster_id = str(config()["BROADCASTER_ID"])
    sa_api_key = str(config()["SA_API_KEY"])
    sermonaudio.set_api_key(f"{sa_api_key}")
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
    if series:
        message(saae, f"Series supplied: {series}")
        series_id = get_series_id(f"{series}")
        if series_id:
            message(saae, f'Series exists, adding {response.sermon_id} to "{series}".')
            add_to_series = Broadcaster.move_sermon_to_series(
                sermon_id=response.sermon_id, series_id=str(series_id)
            )
            if add_to_series:
                message(
                    saae, f'Sermon ID {response.sermon_id} added to series "{series}".'
                )
            else:
                message(
                    saae,
                    f"Unable to add sermon to series, this will need to be done manually via the website.",
                )
        else:
            message(saae, f'Series "{series}" does not exist, creating.')
            series_create_response = Broadcaster.create_series(
                title=f"{series}", broadcaster_id=f"{broadcaster_id}"
            )
            if series_create_response:
                series_id = get_series_id(f"{series}")
                message(
                    saae,
                    f'Series "{series}" Created, adding {response.sermon_id} to it.',
                )
                add_to_series = Broadcaster.move_sermon_to_series(
                    sermon_id=response.sermon_id, series_id=series_id
                )
                if add_to_series:
                    message(
                        saae,
                        f'Sermon ID {response.sermon_id} added to series "{series}".',
                    )
                else:
                    message(
                        saae,
                        "Series created, but adding sermon to it failed. "
                        "This will need to be done manually via the website.",
                    )
            else:
                message(
                    saae,
                    "Unable to create series. This will need to be performed manually via the website. "
                    "After the series has been created, the sermon will need to be added to it manually as well.",
                )
    if response.sermon_id:
        message(saae, f"Sermon Creation Success. SermonID: {response.sermon_id}")
        return response.sermon_id
    else:
        message(saae, f"[ERROR] Sermon Creation Failed.\nError:\n{response}")


def upload_audio(sermon_id, path):
    sa_api_key = str(config()["SA_API_KEY"])
    sermonaudio.set_api_key(f"{sa_api_key}")
    Broadcaster.upload_audio(sermon_id=sermon_id, path=path)
