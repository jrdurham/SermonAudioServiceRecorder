import os
import sounddevice as sd
import numpy as np
import wave
from threading import Thread
from pydub import AudioSegment
import shutil
import filecmp

class AudioRecorder:
    def __init__(self, output_filename="", title="", artist="", album="", comments=""):
        self.output_filename = output_filename
        self.title = title
        self.artist = artist
        self.album = album
        self.comments = comments
        self.is_recording = False
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
                if hostDev['hostapi'] == api and "Headset Microphone" in hostDev['name']:
                    dev= hostDev['index']


            # Use the default input device
            device_info = sd.query_devices(device=dev)
            channels = device_info['max_input_channels']
            fs = device_info['default_samplerate']

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

        outFile=f"{os.getenv('AUDIO_DIR')}{self.output_filename}.mp3"

        audio.export(f"{outFile}", format="mp3", tags={
            'title': f"{self.title}",
            'artist': f"{self.artist}",
            'album': f"{self.album}",
            'comment': f"{self.comments}"
        })
        os.remove("temp.wav")
