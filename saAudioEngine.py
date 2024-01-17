import os
import queue
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
from requests import Session

import saapi
from sasrconfig import config

assert np

_session = Session()
SA_API_KEY = config()["SA_API_KEY"]
q = queue.Queue()


def default():
    apis = api_list()
    sd_default = sd.query_devices(kind="input")
    dev_index = sd_default["index"]
    dev_name = sd_default["name"]
    dev_api = sd_default["hostapi"]
    return str(f"{dev_index}: {dev_name} ({apis.get(dev_api)})")


def dev_list():
    sd_dev_list = {}
    devices = []
    for host_device in sd.query_devices():
        if host_device["max_input_channels"] > 0:
            dev_index = host_device["index"]
            dev_name = host_device["name"]
            dev_api = host_device["hostapi"]
            api_name = api_list().get(dev_api)
            sd_dev_list[dev_index] = (dev_name, dev_api, api_name)
            devices.append(f"{dev_index}: {dev_name} ({api_name})")
    return devices


def api_list():
    api = 0
    sd_api_list = {}
    for host_api in sd.query_hostapis():
        api_name = host_api["name"]
        sd_api_list.update({api: f"{api_name}"})
        api = api + 1
    return sd_api_list


def rec_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


class AudioHandler:
    def __init__(
        self,
        sar_instance,
        file_name="",
        sa_upload=None,
        full_title="",
        speaker_name="",
        preach_date="",
        event_type="",
        bible_text="",
        series="",
        sa_status=False,
    ):
        self.sar = sar_instance
        self.file_name = file_name
        self.is_recording = False
        self.sa_upload = sa_upload
        self.full_title = full_title
        self.speaker_name = speaker_name
        self.preach_date = preach_date
        self.event_type = event_type
        self.bible_text = bible_text
        self.series = series
        self.sa_status = sa_status
        self.tmp_file = None
        self.outfile = None

    def message(self, info):
        self.sar.write_console(f"[AudioEngine] {info}")
        print(f"[AudioEngine] {info}")

    def record_audio(self):
        if "AUDIO_DEVICE" in config():
            audio_dev_id = int(str(config()["AUDIO_DEVICE"]).split(":")[0])
            device_info = sd.query_devices(device=audio_dev_id)
        else:
            device_info = sd.query_devices(kind="input")
        self.message("Initializing Audio Engine...")
        dev = device_info["index"]
        channels = device_info["max_input_channels"]
        fs = int(device_info["default_samplerate"])
        self.message(
            f"Audio Device Information:\n\n  "
            f"Device Name: {device_info['name']}\n  "
            f"Channels: {channels}\n  "
            f"Sample Rate: {fs}\n"
        )
        tmp_file = tempfile.mktemp(prefix="temp_saae", suffix=".wav", dir="")
        self.tmp_file = tmp_file
        try:
            with sf.SoundFile(
                tmp_file, mode="x", samplerate=fs, channels=channels
            ) as file:
                with sd.InputStream(
                    samplerate=fs,
                    device=dev,
                    channels=channels,
                    callback=rec_callback,
                ):
                    self.message("Recording audio.")
                    while self.is_recording:
                        file.write(q.get())
        except KeyboardInterrupt:
            self.message("Recording finished: " + repr(tmp_file))
        finally:
            self.save_audio()
            self.message("Ready to record.")

    def save_audio(self):
        audio_path = config()["AUDIO_PATH"]
        self.message("Recording stopped. Beginning file export.")
        self.message("Validating destination path.")
        if not os.path.exists(f"{audio_path}"):
            self.message("Destination path does not exist...")
            try:
                Path(f"{audio_path}").mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                self.message(
                    f"Unable to create {audio_path} directory. Saving to repo directory."
                )
                audio_path = "."
            else:
                self.message(f"Created {audio_path} directory, saving file.")
        else:
            self.message("Destination path valid, saving audio file.")

        audio = AudioSegment.from_wav(f"{self.tmp_file}")
        fade_in_duration = 5000  # in milliseconds
        fade_out_duration = 5000  # in milliseconds
        audio = audio.fade_in(fade_in_duration).fade_out(fade_out_duration)
        corrected_file_name = str(f"{self.file_name}").replace(" - ", " ")
        if config()["APPEND_TIMESTAMP"] == "TRUE" or os.path.isfile(
            f"{audio_path}/{corrected_file_name}.mp3"
        ):
            corrected_file_name = (
                f"{corrected_file_name}_{int(round(datetime.now().timestamp()))}"
            )
        outfile = f"{audio_path}/{corrected_file_name}.mp3"
        self.outfile = outfile
        audio.export(
            f"{outfile}",
            format="mp3",
            tags={
                "title": f"{self.full_title}",
                "artist": f"{self.speaker_name}",
                "album": f"{self.bible_text}",
                "comment": f"{self.series}",
            },
        )
        self.message(f"Audio File: {outfile}")
        os.remove(f"{self.tmp_file}")
        if self.sa_upload:
            if not self.sa_status:
                self.message(
                    "Sermon marked for SermonAudio upload, but configuration is invalid. Skipping upload."
                )
            elif not self.full_title:
                self.message(
                    "Sermon marked for upload, but the Title field is empty (required). Skipping upload."
                )
            elif not self.speaker_name:
                self.message(
                    "Sermon marked for upload, but the Speaker field is empty (required). Skipping upload."
                )
            elif self.sa_upload and self.sa_status:
                self.message("Sermon Marked for SermonAudio upload, beginning process.")
                sermon_id = saapi.create_sermon(
                    self,
                    self.full_title,
                    self.speaker_name,
                    self.preach_date,
                    self.event_type,
                    self.bible_text,
                    self.series,
                )

                response = saapi.upload_audio(sermon_id, outfile)
                if not response:
                    self.message(
                        f"Media upload successful."
                        f"\n\n"
                        f"  Dashboard URL:\n"
                        f"  https://www.sermonaudio.com/dashboard/sermons/{sermon_id}/"
                        f"\n\n"
                        f"  Public URL:\n"
                        f"  https://www.sermonaudio.com/sermoninfo.asp?SID={sermon_id}\n"
                        "   NOTE: Public URL will not be live for another 5 minutes.\n"
                    )
                self.sar.update_series_field()
                self.sar.seriesField.set(value=f"{self.series}")
        else:
            self.message("Sermon not marked for upload.")
