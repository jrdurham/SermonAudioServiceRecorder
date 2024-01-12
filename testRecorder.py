import tkinter as tk
import sounddevice as sd
import numpy as np
import wave
from threading import Thread


class AudioRecorder:
    def __init__(self, master):
        self.master = master
        self.master.title("Audio Recorder")
        self.master.geometry("400x200")
        self.master.configure(bg="#2B2B2B")

        self.is_recording = False
        self.output_filename = "output.wav"

        self.label = tk.Label(master, text="Audio Recorder", font=("Helvetica", 16), bg="#2B2B2B", fg="white")
        self.label.pack(pady=20)

        self.filename_label = tk.Label(master, text="File Name:", bg="#2B2B2B", fg="white")
        self.filename_label.pack()

        self.filename_entry = tk.Entry(master)
        self.filename_entry.pack()

        self.record_button = tk.Button(master, text="Record", command=self.toggle_recording, bg="#4CAF50", fg="white")
        self.record_button.pack(pady=10)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.config(text="Stop", bg="#FF4500")

        self.output_filename = self.filename_entry.get() + ".wav"

        self.audio_thread = Thread(target=self.record_audio)
        self.audio_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.record_button.config(text="Record", bg="#4CAF50")

    def record_audio(self):
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

        self.save_audio(np.concatenate(frames))

    def save_audio(self, frames):
        frames_scaled = frames * (2**31 - 1)  # Scale the frames to fit within the valid range

        with wave.open(self.output_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(np.dtype(np.int32).itemsize)  # Use int32 for scaled frames
            wf.setframerate(44100)
            wf.writeframes(frames_scaled.astype(np.int32).tobytes())

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorder(root)
    root.mainloop()
