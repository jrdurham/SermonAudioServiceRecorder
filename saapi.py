import sermonaudio
from datetime import datetime, timedelta
from sasrconfig import config
from sermonaudio.node.requests import Node
from sermonaudio.broadcaster.requests import Broadcaster
from sermonaudio import models


def oldmessage(saae, info):
    print(f"[saapi] {info}")


def message(saae, info):
    saae.sar.write_console(f"[API] {info}\n")
    print(f"[saAudioEngine] {info}")


def get_series_titles():
    page = 1
    titles = []
    if "BROADCASTER_ID" in config():
        while True:
            response = Node.get_series_list(
                broadcaster_id=f"{config()["BROADCASTER_ID"]}", page=page, page_size=5
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
    page = 1
    while True:
        response = Node.get_series_list(
            broadcaster_id=f"{config()["BROADCASTER_ID"]}", page=page, page_size=5
        )
        for series in response.results:
            if series.title == f"{series_name}":
                return series.series_id
        if response.next_url:
            page += 1
        else:
            return False


def create_sermon(saae,
    full_title, speaker_name, preach_date, event_type, bible_text, series=None
):
    api_key = f"{config()["SA_API_KEY"]}"
    sermonaudio.set_api_key(api_key)
    response = Broadcaster.create_or_update_sermon(
        full_title=full_title,
        speaker_name=speaker_name,
        publish_timestamp=datetime.now() + timedelta(days=1),
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
            message(saae, f"Series exists, adding {response.sermon_id} to \"{series}\".")
            add_to_series = Broadcaster.move_sermon_to_series(sermon_id=response.sermon_id, series_id=str(series_id))
            if add_to_series:
                message(saae, f"Sermon ID {response.sermon_id} added to series \"{series}\".")
            else:
                message(saae, f"Unable to add sermon to series, this will need to be done manually via the website.")
        else:
            message(saae, f"Series \"{series}\" does not exist, creating.")
            series_create_response = Broadcaster.create_series(
                title=f"{series}", broadcaster_id=f"{config()["BROADCASTER_ID"]}"
            )
            if series_create_response:
                series_id = get_series_id(f"{series}")
                message(saae, f"Series \"{series}\" Created, adding {response.sermon_id} to it.")
                add_to_series = Broadcaster.move_sermon_to_series(sermon_id=response.sermon_id, series_id=series_id)
                if add_to_series:
                    message(saae, f"Sermon ID {response.sermon_id} added to series \"{series}\".")
                else:
                    message(saae, "Series created, but adding sermon to it failed. "
                            "This will need to be done manually via the website.")
            else:
                message(saae, "Unable to create series. This will need to be performed manually via the website. "
                        "After the series has been created, the sermon will need to be added to it manually as well.")
    if response.sermon_id:
        message(saae, f"Sermon Creation Success. SermonID: {response.sermon_id}")
        return response.sermon_id
    else:
        message(saae, f"[ERROR] Sermon Creation Failed.\nError:\n{response}")


def upload_audio(sermon_id, path):
    sa_api_key = f"{config()["SA_API_KEY"]}"
    sermonaudio.set_api_key(sa_api_key)
    Broadcaster.upload_audio(sermon_id=sermon_id, path=path)
