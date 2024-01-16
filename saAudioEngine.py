import os
import numpy as np
import queue
import saapi
import sounddevice as sd
import soundfile as sf
import sys
import tempfile
from pathlib import Path
from pydub import AudioSegment
from requests import Session
from sasrconfig import config
assert np

_session = Session()
SA_API_KEY = config()["SA_API_KEY"]
q = queue.Queue()


def message(message):
    print(f"[saAudioEngine] {message}")


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
        api_index = api
        api_name = host_api["name"]
        sd_api_list.update({api:f"{api_name}"})
        api = api + 1
    return sd_api_list


class AudioHandler:
    def __init__(
        self,
        fileName="",
        saUpload=None,
        fullTitle="",
        speakerName="",
        publishTimestamp="",
        preachDate="",
        eventType="",
        bibleText="",
        series="",
    ):
        self.fileName = fileName
        self.is_recording = False
        self.saUpload = saUpload
        self.fullTitle = fullTitle
        self.speakerName = speakerName
        self.publishTimestamp = publishTimestamp
        self.preachDate = preachDate
        self.eventType = eventType
        self.bibleText = bibleText
        self.series = series

    def recCallback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    def recordAudio(self):
        if "AUDIO_DEVICE" in config():
            audio_dev_id = int(str(config()["AUDIO_DEVICE"]).split(':')[0])
            device_info = sd.query_devices(device=audio_dev_id)
        else:
            device_info = sd.query_devices(kind="input")
        message("Initializing Audio Engine...")
        dev = device_info["index"]
        channels = device_info["max_input_channels"]
        fs = int(device_info["default_samplerate"])
        message(
            f"Audio Device Information:\n\n  Device Name: {device_info['name']}\n  Channels: {channels}\n  Sample Rate: {fs}\n"
        )
        try:
            tmpFile = tempfile.mktemp(
                prefix="temp_saae", suffix=".wav", dir=""
            )
            self.tmpFile = tmpFile
            with sf.SoundFile(
                tmpFile, mode="x", samplerate=fs, channels=channels
            ) as file:
                with sd.InputStream(
                    samplerate=fs,
                    device=dev,
                    channels=channels,
                    callback=self.recCallback,
                ):
                    message("Recording audio.")
                    while self.is_recording:
                        file.write(q.get())
        except KeyboardInterrupt:
            message("Recording finished: " + repr(tmpFile))
        finally:
            self.saveAudio()
            message("Ready to record.")

    def saveAudio(self):
        audio_path = config()["AUDIO_PATH"]
        message("Recording stopped. Beginning file export.")
        message("Validating destination path.")
        if not os.path.exists(f"{audio_path}"):
            message("Destination path does not exist...")
            try:
                Path(f"{audio_path}").mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                message(f"Unable to create {config()["AUDIO_PATH"]} directory. Saving to repo directory.")
                audio_path = "."

        audio = AudioSegment.from_wav(f"{self.tmpFile}")
        fade_in_duration = 5000  # in milliseconds
        fade_out_duration = 5000  # in milliseconds
        audio = audio.fade_in(fade_in_duration).fade_out(fade_out_duration)
        outFile = f"{audio_path}/{self.fileName}.mp3"
        self.outFile = outFile
        audio.export(
            f"{outFile}",
            format="mp3",
            tags={
                "title": f"{self.fullTitle}",
                "artist": f"{self.speakerName}",
                "album": f"{self.bibleText}",
                "comment": f"{self.series}",
            },
        )
        message(f"Audio File: {outFile}")
        os.remove(f"{self.tmpFile}")
        if self.saUpload:
            message("Sermon Marked for SermonAudio upload, beginning process.")
            sermonid = saapi.create_sermon(
                self.fullTitle,
                self.speakerName,
                self.publishTimestamp,
                self.preachDate,
                self.eventType,
                self.bibleText,
            )

            response = saapi.upload_audio(sermonid, outFile)
            if not response:
                message(
                    f"Media upload successful."
                    f"\n\n"
                    f"  Dashboard URL:\n"
                    f"  https://www.sermonaudio.com/dashboard/sermons/{sermonid}/"
                    f"\n\n"
                    f"  Public URL:\n"
                    f"  https://www.sermonaudio.com/sermoninfo.asp?SID={sermonid}\n"
                    "   NOTE: Public URL will not be live for another 5 minutes.\n"
                )
