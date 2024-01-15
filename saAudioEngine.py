import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import saapi
import requests
import json
import tempfile
import queue
import sys
from requests import Session
from datetime import datetime
from pydub import AudioSegment
from dotenv import load_dotenv

assert np

import logging

l = logging.getLogger("pydub.converter")
l.setLevel(logging.ERROR)
l.addHandler(logging.StreamHandler())


_session = Session()

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

SA_API_KEY = os.getenv("SA_API_KEY")

q = queue.Queue()


def message(message):
    print(f"[saAudioEngine] {message}")

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
        message("Initializing Audio Engine...")
        device_info = sd.query_devices(kind="input")
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
        message("Recording stopped. Beginning file export.")
        audio = AudioSegment.from_wav(f"{self.tmpFile}")

        fade_in_duration = 5000  # in milliseconds
        fade_out_duration = 5000  # in milliseconds
        audio = audio.fade_in(fade_in_duration).fade_out(fade_out_duration)
        outFile = f"{os.getenv('AUDIO_DIR')}{self.fileName}.mp3"
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
