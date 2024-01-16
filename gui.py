import sys

import customtkinter
import saapi
import time
from datetime import datetime
from PIL import Image
import saAudioEngine as saae
from saAudioEngine import AudioHandler as ah
from sasrconfig import config
from threading import Thread

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")
logoImg = customtkinter.CTkImage(
    light_image=None, dark_image=Image.open(config()["GUI_LOGO"]), size=(160, 35)
)
dateNow = datetime.now()
fullDateStamp = datetime.today().strftime("%Y%m%d")


class SettingsGUI(customtkinter.CTkToplevel):
    save_args = {}

    def __init__(self, sa_recorder_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sa_recorder_instance = sa_recorder_instance
        self.title("Service Recorder Settings")
        self.geometry(f"{490}x{400}")
        self.after(10, self.lift)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(5, weight=1)
        self.top_label = customtkinter.CTkLabel(self, text="Service Recorder Settings")
        self.top_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="new")
        self.broadcaster_label = customtkinter.CTkLabel(self, text="Member ID:")
        self.broadcaster_label.grid(row=1, column=0, padx=(20,10), pady=(10), sticky="w")
        self.broadcaster_field = customtkinter.CTkEntry(self, placeholder_text="")
        self.broadcaster_field.grid(row=1, column=1, padx=(10,20), pady=10, sticky="we")
        self.apikey_label = customtkinter.CTkLabel(self, text="API Key:")
        self.apikey_label.grid(row=2, column=0, padx=(20,10), pady=(10), sticky="w")
        self.apikey_field = customtkinter.CTkEntry(self, placeholder_text="Listed at SermonAudio members only area.")
        self.apikey_field.grid(row=2, column=1, padx=(10,20), pady=10, sticky="we")
        self.device_label = customtkinter.CTkLabel(self, text="Audio Input Device:")
        self.device_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
        self.device_field = customtkinter.CTkOptionMenu(self, values=saae.dev_list())
        self.device_field.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="we")
        self.audio_path_label = customtkinter.CTkLabel(self, text="Audio File Path:")
        self.audio_path_label.grid(row=4, column=0, padx=(20,10), pady=(10), sticky="w")
        self.audio_path_field = customtkinter.CTkEntry(self, placeholder_text="Defaults to ./recordings.")
        self.audio_path_field.grid(row=4, column=1, padx=(10,20), pady=10, sticky="we")
        self.save_button = customtkinter.CTkButton(self, text="Save Settings", command=self.save_exit)
        self.save_button.grid(row=5, column=0, columnspan=2, pady=10, sticky="s")

        if "BROADCASTER_ID" in config() and len(config()["BROADCASTER_ID"]) > 0:
            self.broadcaster_field.insert(0, f"{config()["BROADCASTER_ID"]}")
        else:
            pass

        if "SA_API_KEY" in config() and len(config()["SA_API_KEY"]) == 36:
            self.apikey_field.insert(0, f"{config()["SA_API_KEY"]}")
        else:
            pass

        if "AUDIO_DEVICE" in config():
            self.device_field.set(f"{config()["AUDIO_DEVICE"]}")
        else:
            self.device_field.set(value=f"{saae.default()}")

        if "AUDIO_PATH" in config():
            self.audio_path_field.insert(0, f"{config()["AUDIO_PATH"]}")
        else:
            pass

    def save_exit(self):
        self.save_args.update({
            "BROADCASTER_ID": f"{self.broadcaster_field.get()}",
            "SA_API_KEY": f"{self.apikey_field.get()}",
            "AUDIO_DEVICE": f"{self.device_field.get()}",
            "AUDIO_PATH": f"{self.audio_path_field.get()}"
        })
        config(**self.save_args)
        self.destroy()
        self.sa_recorder_instance.update_series_field()
        pass


class saRecorder(customtkinter.CTk):
    def __init__(self):
        # Initialize config
        config()
        super().__init__()

        self.settings_gui = None
        self.engine = ah(self)
        self.deCheck = customtkinter.StringVar(value="on")
        self.fileName = "init"
        self.sermon_id = None

        # configure window
        self.title("Service Recorder")
        self.geometry(f"{760}x{580}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 0), weight=0)
        self.grid_rowconfigure((2), weight=1)
        # self.grid_rowconfigure(1, weight=2)

        # Sidebar
        self.sidebarFrame = customtkinter.CTkFrame(self, corner_radius=0)
        self.sidebarFrame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebarFrame.columnconfigure(1, weight=1)
        self.sidebarFrame.rowconfigure(7, weight=1)
        self.logo = customtkinter.CTkLabel(self.sidebarFrame, image=logoImg, text="")
        self.logo.grid(row=0, column=0, pady=(25, 15), columnspan=2)
        self.title_label = customtkinter.CTkLabel(
            self.sidebarFrame,
            text="Service Recorder",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.title_label.grid(row=1, column=0, padx=20, pady=(0, 10), columnspan=2)
        self.recordButton = customtkinter.CTkButton(
            self.sidebarFrame, text="Begin Recording", command=self.recording
        )
        self.recordButton.grid(row=2, column=0, padx=20, pady=10, columnspan=2)
        self.saUpload = customtkinter.CTkCheckBox(
            self.sidebarFrame, text="Upload to SermonAudio", command=None
        )
        self.saUpload.grid(row=3, column=0, padx=20, pady=10, sticky="w", columnspan=2)
        self.saUpload.select()
        self.manualDateEvent = customtkinter.CTkSwitch(
            self.sidebarFrame,
            text="Automatically Set Date/Event",
            command=self.userSetDateEvent,
            onvalue="on",
            offvalue="off",
            variable=self.deCheck,
        )
        self.manualDateEvent.grid(
            row=4, column=0, padx=20, pady=10, sticky="w", columnspan=2
        )
        self.manualEventLabel = customtkinter.CTkLabel(self.sidebarFrame, text="Event:")
        self.manualEventLabel.grid(row=5, column=0, padx=(20, 10), pady=10, sticky="w")
        self.manualEvent = customtkinter.CTkOptionMenu(
            self.sidebarFrame,
            values=[
                "Sunday - AM",
                "Sunday - PM",
                "Sunday School",
                "Midweek Service",
                "Special Meeting",
                "Camp Meeting",
            ],
        )
        self.manualEvent.grid(
            row=5, column=1, padx=(10, 20), pady=10, columnspan=2, sticky="we"
        )
        self.manualEvent.set(f"{self.eventType()}")
        self.manualEvent.configure(state="disabled")
        self.manualDateLabel = customtkinter.CTkLabel(self.sidebarFrame, text="Date:")
        self.manualDateLabel.grid(row=6, column=0, padx=(20, 10), pady=10, sticky="w")
        self.manualDateLabel.configure(state="disabled")
        self.manualDate = customtkinter.CTkEntry(
            self.sidebarFrame, textvariable=customtkinter.StringVar(value=f"{fullDateStamp}")
        )
        self.manualDate.grid(row=6, column=1, padx=(10, 20), pady=20, sticky="ew")
        self.manualDate.configure(state="disabled")
        self.manualDate.configure(text_color="gray62")
        self.settings_gui_button = customtkinter.CTkButton(
            self.sidebarFrame,
            text="Settings",
            command=self.open_settings,
        )
        self.settings_gui_button.grid(row=7, column=0, padx=20, pady=10, columnspan=2, sticky="s")

        # Required Tags
        self.reqTagsFrame = customtkinter.CTkFrame(self)
        self.reqTagsFrame.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nwes")
        self.reqTagsFrame.columnconfigure(1, weight=1)
        self.frameLabel = customtkinter.CTkLabel(
            self.reqTagsFrame, text="Required Parameters"
        )
        self.frameLabel.grid(
            row=0, column=0, padx=20, pady=(5, 0), sticky="new", columnspan=2
        )
        self.sermonLabel = customtkinter.CTkLabel(
            self.reqTagsFrame, text="Sermon Title:"
        )
        self.sermonLabel.grid(row=1, column=0, padx=(10, 0), pady=(20, 0), sticky="w")
        self.sermonField = customtkinter.CTkEntry(
            self.reqTagsFrame,
            placeholder_text="Example: The Gift of Eternal Life",
            width=290,
        )
        self.sermonField.grid(row=1, column=1, padx=20, pady=(20, 0), sticky="nse")
        self.speakerLabel = customtkinter.CTkLabel(self.reqTagsFrame, text="Speaker:")
        self.speakerLabel.grid(row=2, column=0, padx=(10, 0), pady=(20, 0), sticky="w")
        self.speakerField = customtkinter.CTkEntry(
            self.reqTagsFrame, placeholder_text="Example: Johnny Clardy", width=290
        )
        self.speakerField.grid(row=2, column=1, padx=(20), pady=20, sticky="nse")

        # Optional Tags
        self.optTagsFrame = customtkinter.CTkFrame(self)
        self.optTagsFrame.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="nwe")
        self.optTagsFrame.columnconfigure(1, weight=1)
        self.frameLabel = customtkinter.CTkLabel(
            self.optTagsFrame, text="Optional Parameters"
        )
        self.frameLabel.grid(
            row=0, column=0, padx=20, pady=(5, 0), sticky="new", columnspan=2
        )
        self.refLabel = customtkinter.CTkLabel(
            self.optTagsFrame, text="Text Reference:"
        )
        self.refLabel.grid(row=1, column=0, padx=(10, 0), pady=(20, 0), sticky="w")
        self.refField = customtkinter.CTkEntry(
            self.optTagsFrame, placeholder_text="Example: 2 Corinthians 9; Romans 5", width=290
        )
        self.refField.grid(row=1, column=1, padx=20, pady=(20, 0), sticky="nse")
        self.seriesLabel = customtkinter.CTkLabel(
            self.optTagsFrame, text="Series Title:"
        )
        self.seriesLabel.grid(row=2, column=0, padx=(10, 0), pady=(20, 20), sticky="w")
        self.seriesField = customtkinter.CTkComboBox(
            self.optTagsFrame, width=290, values=saapi.get_series_titles()
        )
        self.seriesField.set("")
        self.seriesField.grid(row=2, column=1, padx=20, pady=(20, 20), sticky="nse")

        # Console Output
        self.console = customtkinter.CTkTextbox(self)
        self.console.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.console.configure(state="disabled")

    # Functions
    def recording(self):
        self.fileName = f"{fullDateStamp}-{self.manualEvent.get()}"
        self.engine.is_recording = True
        Thread(target=self.engine.recordAudio).start()
        self.recordButton.configure(
            text="End Recording",
            fg_color="dark red",
            hover_color="#590000",
            command=self.notRecording,
        )

    def notRecording(self):
        self.console.focus()
        self.recordButton.configure(
            text="Begin Recording",
            fg_color=("#3B8ED0", "#1F6AA5"),
            hover_color=("#36719F", "#144870"),
            command=self.recording,
        )
        if str(self.deCheck.get()) == "off":
            self.fileName = (
                f"{self.manualDate.get()}-{self.manualEvent.get()}"
            )
        self.engine.fileName = f"{self.fileName}"
        self.engine.is_recording = False
        self.engine.fullTitle = f"{self.sermonField.get()}"
        self.engine.speakerName = f"{self.speakerField.get()}"
        self.engine.bibleText = f"{self.refField.get()}"
        self.engine.series = f"{self.seriesField.get()}"
        self.engine.preachDate = (
            self.manualDate.get() if str(self.deCheck.get()) == "off" else fullDateStamp
        )
        self.engine.eventType = f"{self.manualEvent.get()}"
        if self.saUpload.get() == 1:
            self.engine.saUpload = f"{self.saUpload.get()}"

    def userSetDateEvent(self):
        self.manualEvent.configure(
            state="normal" if str(self.deCheck.get()) == "off" else "disabled"
        )
        self.manualDate.configure(
            state="normal" if str(self.deCheck.get()) == "off" else "disabled"
        )
        self.manualDate.configure(
            text_color="#DCE4EE" if str(self.deCheck.get()) == "off" else "gray62"
        )


    def open_settings(self):
        if self.settings_gui is None or not self.settings_gui.winfo_exists():
            self.settings_gui = SettingsGUI(self, self)
            time.sleep(1)
            self.settings_gui.lift()
        else:
            self.settings_gui.focus()

    def printFileName(self):
        print(self.fileName)

    def eventType(self):
        if dateNow.weekday() == 6 and dateNow.hour < 11:
            eventType = "Sunday School"
        elif dateNow.weekday() == 6 and dateNow.hour >= 11 and dateNow.hour <= 14:
            eventType = "Sunday AM"
        elif dateNow.weekday() == 6 and dateNow.hour >= 17:
            eventType = "Sunday PM"
        elif dateNow.weekday() == 2 and dateNow.hour >= 18:
            eventType = "Midweek Service"
        else:
            eventType = "Special Meeting"
        return eventType

    def timeStamp(self):
        return int(round(datetime.now().timestamp()))

    def update_series_field(self):
        self.seriesField.configure(values=saapi.get_series_titles())

    def write_console(self, output):
        self.console.configure(state="normal")
        self.console.insert(customtkinter.END, output)
        self.console.configure(state="disabled")
        self.console.see(customtkinter.END)


if __name__ == "__main__":
    sar = saRecorder()
    sar.iconbitmap(config()["GUI_ICO"])
    sar.mainloop()
