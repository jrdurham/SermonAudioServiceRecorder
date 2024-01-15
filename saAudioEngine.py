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
        device_info = sd.query_devices(kind="input")
        dev = device_info["index"]
        channels = device_info["max_input_channels"]
        fs = int(device_info["default_samplerate"])
        print(
            f"Device Name: {device_info['name']}\nChannels: {channels}\nSample Rate: {fs}"
        )
        try:
            tmpFile = tempfile.mktemp(
                prefix="delme_rec_unlimited_", suffix=".wav", dir=""
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
                    while self.is_recording:
                        file.write(q.get())
        except KeyboardInterrupt:
            print("\nRecording finished: " + repr(tmpFile))
        finally:
            self.saveAudio()

    def saveAudio(self):
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
        os.remove(f"{self.tmpFile}")
        if self.saUpload:
            sermonid = saapi.create_sermon(
                self.fullTitle,
                self.speakerName,
                self.publishTimestamp,
                self.preachDate,
                self.eventType,
                self.bibleText,
            )
            response = saapi.upload_audio(sermonid, outFile)
            print(response)

    def createSermon(self):
        # Print variables before making the API call
        print("Variables passed to createSermon:")
        print(f"fullTitle: {self.fullTitle}")
        print(f"speakerName: {self.speakerName}")
        print(f"publishTimestamp: {self.publishTimestamp}")
        print(f"preachDate: {self.preachDate}")
        print(f"eventType: {self.eventType}")
        print(f"bibleText: {self.bibleText}")

        url = "https://api.sermonaudio.com/v2/node/sermons"

        headers = {
            "accept": "application/json",
            "X-API-Key": SA_API_KEY,
            "Content-Type": "application/json",
        }

        sermon_data = {
            "acceptCopyright": True,
            "fullTitle": f"{self.fullTitle}",
            "speakerName": f"{self.speakerName}",
            "publishTimestamp": self.publishTimestamp,
            "displayTitle": "",  # You can customize or add more parameters as needed
            "subtitle": "",
            "languageCode": "en",
            "newsInFocus": False,
            "preachDate": f"{self.preachDate}",
            "eventType": f"{self.eventType}",
            "bibleText": f"{self.bibleText}",
            "moreInfoText": "",
            "keywords": "",
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(sermon_data))

            if response.status_code == 200 or 201:
                sermon_id = response.json().get("sermonID")
                self.sermonId = sermon_id
                print(f"Sermon created successfully with ID: {sermon_id}")
                self.createMedia()
                return sermon_id
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error: {e}")

    def createMedia(self):
        url = "https://api.sermonaudio.com/v2/media"

        headers = {
            "accept": "application/json",
            "X-API-Key": SA_API_KEY,
            "Content-Type": "application/json",
        }

        data = {
            "uploadType": "original",
            "sermonID": f"{self.sermonId}",
            "originalFilename": f"{self.fileName}",
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200 or 201:
                print(response)
                uploadURL = response.json().get("uploadURL")
                self.uploadURL = uploadURL
                print(f"Upload URL: {uploadURL}")
                self.uploadMedia()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error: {e}")

    def uploadMedia(self):
        url = f"{self.uploadURL}"
        file_path = f"{self.outFile}"

        header = {"X-API-Key": SA_API_KEY}

        file = {"file": open(file_path, "rb")}
        with open(file_path, "rb") as fp:
            try:
                response = _session.post(url, data=fp, stream=True, headers=header)
                if response.status_code == 200 or 201:
                    print(response.text)
                else:
                    print(f"Error: {response.status_code}")
                    print(response.text)
            except Exception as e:
                print(f"Error: {e}")
