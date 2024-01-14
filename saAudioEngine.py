import os
import sounddevice as sd
import soundfile as sf
import numpy as np
assert np
import wave
import shutil
import filecmp
import requests
import json
import tempfile
import queue
import sys
from requests import Session
from threading import Thread
from pydub import AudioSegment
from dotenv import load_dotenv

_session = Session()

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))

SA_API_KEY = os.getenv('SA_API_KEY')

q = queue.Queue()

class AudioHandler:
    def __init__(self, fileName="", saUpload=None, fullTitle="", speakerName="", publishTimestamp="", preachDate="", eventType="", bibleText="", series=""):
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
    def recordAudio(self):
            chunk = 1024
            sample_format = np.float32

            device_info = sd.query_devices()

            i=0
            for hostApi in sd.query_hostapis():
                if "WASAPI" in hostApi["name"]:
                    api=i
                    break
                i = i+1

            for hostDev in sd.query_devices():
                #print(f"Dev ID: {hostDev['index']}\nDev Name: {hostDev['name']}\nHost API: {hostDev['hostapi']}")
                if hostDev['hostapi'] == api and "Onyx" in hostDev['name']:
                    dev= hostDev['index']
                    self.dev = dev


            # Use the default input device
            device_info = sd.query_devices(device=dev)
            channels = device_info['max_input_channels']
            fs = device_info['default_samplerate']
            self.fs = fs

            print(f"Device Name: {device_info['name']}\nChannels: {channels}\nSample Rate: {fs}")

            frames = []

            with sd.InputStream(channels=channels, samplerate=fs, dtype=sample_format) as stream:
                while self.is_recording:
                    data, overflowed = stream.read(chunk)
                    frames.append(data)

            self.saveAudio(np.concatenate(frames))

    def saveAudio(self, frames):
        frames_scaled = frames * (2**31 - 1)  # Scale the frames to fit within the valid range

        with wave.open("temp.wav", 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(np.dtype(np.int32).itemsize)  # Use int32 for scaled frames
            wf.setframerate(44100)
            wf.writeframes(frames_scaled.astype(np.int32).tobytes())

        audio = AudioSegment.from_wav("temp.wav")

        fade_in_duration = 5000  # in milliseconds
        fade_out_duration = 5000  # in milliseconds
        audio = audio.fade_in(fade_in_duration).fade_out(fade_out_duration)

        outFile=f"{os.getenv('AUDIO_DIR')}{self.fileName}.mp3"
        self.outFile = outFile
        audio.export(f"{outFile}", format="mp3", tags={
            'title': f"{self.fullTitle}",
            'artist': f"{self.speakerName}",
            'album': f"{self.bibleText}",
            'comment': f"{self.series}"
        })
        os.remove("temp.wav")
        #if self.saUpload:
        #    self.createSermon()

    def recCallback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    def newRecordAudio(self):

        device_info = sd.query_devices()

        i=0
        for hostApi in sd.query_hostapis():
            if "WASAPI" in hostApi["name"]:
                api=i
                break
            i = i+1

        for hostDev in sd.query_devices():
            #print(f"Dev ID: {hostDev['index']}\nDev Name: {hostDev['name']}\nHost API: {hostDev['hostapi']}")
            if hostDev['hostapi'] == api and "Onyx" in hostDev['name']:
                dev= hostDev['index']
                self.dev = dev


        # Use the default input device
        device_info = sd.query_devices(device=dev)
        channels = device_info['max_input_channels']
        fs = device_info['default_samplerate']
        self.fs = fs

        print(f"Device Name: {device_info['name']}\nChannels: {channels}\nSample Rate: {fs}")

        try:
            tmpFile = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                            suffix='.wav', dir='')
            self.tmpFile = tmpFile
            with sf.SoundFile(tmpFile, mode='x', samplerate=int(self.fs),
                            channels=1) as file:
                with sd.InputStream(samplerate=self.fs, device=self.dev,
                                    channels=1, callback=self.recCallback):
                    while self.is_recording:
                        file.write(q.get())
        except KeyboardInterrupt:
            print('\nRecording finished: ' + repr(tmpFile))
        
    def newSaveAudio(self):
        audio = AudioSegment.from_wav(f"{self.tmpFile}")

        fade_in_duration = 5000  # in milliseconds
        fade_out_duration = 5000  # in milliseconds
        audio = audio.fade_in(fade_in_duration).fade_out(fade_out_duration)
        outFile=f"{os.getenv('AUDIO_DIR')}{self.fileName}.mp3"
        self.outFile = outFile
        audio.export(f"{outFile}", format="mp3", tags={
            'title': f"{self.fullTitle}",
            'artist': f"{self.speakerName}",
            'album': f"{self.bibleText}",
            'comment': f"{self.series}"
        })
        os.remove(f"{self.tmpFile}")

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
            "Content-Type": "application/json"
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
            "keywords": ""
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(sermon_data))

            if response.status_code == 200 or 201:
                sermon_id = response.json().get('sermonID')
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
            "Content-Type": "application/json"
        }

        data = {
            "uploadType": "original",
            "sermonID": f"{self.sermonId}"
            #"originalFilename": f"{self.fileName}"
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200 or 201:
                print(response)
                uploadURL = response.json().get('uploadURL')
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

        file = {'file': open(file_path, 'rb')}
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
