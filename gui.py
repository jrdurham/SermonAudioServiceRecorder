import time
from datetime import datetime
from threading import Thread

import customtkinter
from PIL import Image
import pygit2

import saAudioEngine as saAE
import saapi
from saAudioEngine import AudioHandler
from sasrconfig import config

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Get repo metadata
repo = pygit2.Repository('.')
branch = repo.head.shorthand
commit = str(repo.head.target)

logoImg = customtkinter.CTkImage(
    light_image=None, dark_image=Image.open(config()["GUI_LOGO"]), size=(160, 35)
)
red_status = customtkinter.CTkImage(
    light_image=Image.open("img/red.png"),
    dark_image=Image.open("img/red.png"),
    size=(10, 10),
)
grn_status = customtkinter.CTkImage(
    light_image=Image.open("img/red.png"),
    dark_image=Image.open("img/grn.png"),
    size=(10, 10),
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
        if config()["FIRST_RUN"]:
            self.after(1600, self.lift)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(5, weight=1)
        self.top_label = customtkinter.CTkLabel(self, text="Service Recorder Settings")
        self.top_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="new")
        self.broadcaster_label = customtkinter.CTkLabel(self, text="Member ID:")
        self.broadcaster_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        self.broadcaster_field = customtkinter.CTkEntry(
            self, placeholder_text="Listed at SermonAudio members only area."
        )
        self.broadcaster_field.grid(
            row=1, column=1, padx=(10, 20), pady=10, sticky="we"
        )
        self.apikey_label = customtkinter.CTkLabel(self, text="API Key:")
        self.apikey_label.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="w")
        self.apikey_field = customtkinter.CTkEntry(
            self, placeholder_text="Listed at SermonAudio members only area.", show="•"
        )
        self.apikey_field.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="we")
        self.device_label = customtkinter.CTkLabel(self, text="Audio Input Device:")
        self.device_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
        self.device_field = customtkinter.CTkOptionMenu(self, values=saAE.dev_list())
        self.device_field.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="we")
        self.audio_path_label = customtkinter.CTkLabel(self, text="Audio File Path:")
        self.audio_path_label.grid(row=4, column=0, padx=(20, 10), pady=10, sticky="w")
        self.audio_path_field = customtkinter.CTkEntry(
            self, placeholder_text="Defaults to ./recordings."
        )
        self.audio_path_field.grid(row=4, column=1, padx=(10, 20), pady=10, sticky="we")
        self.save_button = customtkinter.CTkButton(
            self, text="Save Settings", command=self.save_exit
        )
        self.save_button.grid(row=5, column=0, columnspan=2, pady=10, sticky="s")

        broadcaster_id = config()["BROADCASTER_ID"]
        sa_api_key = config()["SA_API_KEY"]
        audio_device = config()["AUDIO_DEVICE"]
        audio_path = config()["AUDIO_PATH"]

        if len(str(config()["BROADCASTER_ID"])) > 0:
            self.broadcaster_field.insert(0, f"{broadcaster_id}")
        else:
            pass

        if len(str(config()["SA_API_KEY"])) == 36:
            self.apikey_field.insert(0, f"{sa_api_key}")
        else:
            pass

        if "AUDIO_DEVICE" in config():
            self.device_field.set(f"{audio_device}")
        else:
            self.device_field.set(value=f"{saAE.default()}")

        if "AUDIO_PATH" in config():
            self.audio_path_field.insert(0, f"{audio_path}")
        else:
            pass

    def save_exit(self):
        self.save_args.update(
            {
                "BROADCASTER_ID": f"{self.broadcaster_field.get()}",
                "SA_API_KEY": f"{self.apikey_field.get()}",
                "AUDIO_DEVICE": f"{self.device_field.get()}",
                "AUDIO_PATH": f"{self.audio_path_field.get()}",
                "FIRST_RUN": False,
            }
        )
        config(**self.save_args)
        self.destroy()
        self.sa_recorder_instance.validate_config()
        pass


class RecorderGui(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.sa_status = None
        self.settings_gui = None
        self.engine = AudioHandler(self)
        self.deCheck = customtkinter.StringVar(value="on")
        self.file_name = "init"
        self.sermon_id = None

        # configure window
        self.title("Service Recorder")
        self.geometry(f"{760}x{580}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 0), weight=0)
        self.grid_rowconfigure(2, weight=1)
        # self.grid_rowconfigure(1, weight=2)

        # Sidebar
        self.sidebarFrame = customtkinter.CTkFrame(self, corner_radius=0)
        self.sidebarFrame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebarFrame.columnconfigure(1, weight=1)
        self.sidebarFrame.rowconfigure(9, weight=1)
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
        self.sa_upload = customtkinter.CTkCheckBox(
            self.sidebarFrame, text="Upload to SermonAudio", command=None
        )
        self.sa_upload.grid(row=3, column=0, padx=20, pady=10, sticky="w", columnspan=2)
        self.sa_upload.select()
        self.manualDateEvent = customtkinter.CTkSwitch(
            self.sidebarFrame,
            text="Automatically Set Date/Event",
            command=self.set_date_event,
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
        self.manualEvent.set(f"{event_type()}")
        self.manualEvent.configure(state="disabled")
        self.manualDateLabel = customtkinter.CTkLabel(self.sidebarFrame, text="Date:")
        self.manualDateLabel.grid(row=6, column=0, padx=(20, 10), pady=10, sticky="w")
        self.manualDateLabel.configure(state="disabled")
        self.manualDate = customtkinter.CTkEntry(
            self.sidebarFrame,
            textvariable=customtkinter.StringVar(value=f"{fullDateStamp}"),
        )
        self.manualDate.grid(row=6, column=1, padx=(10, 20), pady=20, sticky="ew")
        self.manualDate.configure(state="disabled")
        self.manualDate.configure(text_color="gray62")
        self.status_frame = customtkinter.CTkFrame(
            self.sidebarFrame, corner_radius=0, fg_color="transparent"
        )
        self.status_frame.grid(
            row=7, column=0, padx=5, pady=10, columnspan=2, sticky="we"
        )
        self.status_frame.grid_columnconfigure(1, weight=1)
        self.id_status = customtkinter.CTkLabel(
            self.status_frame, image=red_status, text=""
        )
        self.id_status.grid(row=0, column=0, padx=(20, 5), pady=(10, 5), sticky="w")
        self.id_status_label = customtkinter.CTkLabel(
            self.status_frame, text="Member ID Status"
        )
        self.id_status_label.grid(
            row=0, column=1, padx=(5, 20), pady=(10, 5), sticky="w", columnspan=2
        )
        self.api_status = customtkinter.CTkLabel(
            self.status_frame, image=red_status, text=""
        )
        self.api_status.grid(row=1, column=0, padx=(20, 5), pady=(0, 10), sticky="w")
        self.api_status_label = customtkinter.CTkLabel(
            self.status_frame, text="API Key Status"
        )
        self.api_status_label.grid(
            row=1, column=1, padx=(5, 20), pady=(0, 10), sticky="w", columnspan=2
        )
        self.settings_gui_button = customtkinter.CTkButton(
            self.sidebarFrame,
            text="Settings",
            command=self.open_settings,
        )
        self.settings_gui_button.grid(
            row=9, column=0, padx=20, pady=10, columnspan=2, sticky="s"
        )

        # Required Tags
        self.reqTagsFrame = customtkinter.CTkFrame(self)
        self.reqTagsFrame.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nwes")
        self.reqTagsFrame.columnconfigure(1, weight=2)
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
            width=360,
        )
        self.sermonField.grid(row=1, column=1, padx=20, pady=(20, 0), sticky="nse")
        self.speakerLabel = customtkinter.CTkLabel(self.reqTagsFrame, text="Speaker:")
        self.speakerLabel.grid(row=2, column=0, padx=(10, 0), pady=20, sticky="w")
        self.speakerField = customtkinter.CTkEntry(
            self.reqTagsFrame, placeholder_text="Example: Johnny Clardy", width=360
        )
        self.speakerField.grid(row=2, column=1, padx=20, pady=20, sticky="nse")

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
            self.optTagsFrame,
            placeholder_text="Example: 2 Corinthians 9; Romans 5",
            width=360,
        )
        self.refField.grid(row=1, column=1, padx=20, pady=(20, 0), sticky="nse")
        self.seriesLabel = customtkinter.CTkLabel(
            self.optTagsFrame, text="Series Title:"
        )
        self.seriesLabel.grid(row=2, column=0, padx=(10, 0), pady=20, sticky="w")
        self.seriesField = customtkinter.CTkComboBox(
            self.optTagsFrame, width=360, values=saapi.get_series_titles()
        )
        self.seriesField.set("")
        self.seriesField.grid(row=2, column=1, padx=20, pady=(20, 20), sticky="nse")

        # Console Output
        self.console = customtkinter.CTkTextbox(self)
        self.console.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.console.configure(state="disabled")

    def validate_config(self):
        # Print Version Info
        self.write_console(
            f"[ServiceRecorder] Branch: {branch}\n[ServiceRecorder] Commit Hash: {commit[:7]}"
        )

        if "BROADCASTER_ID" not in config() or not len(config()["BROADCASTER_ID"]) > 0:
            self.write_console("[WARNING] SermonAudio Member ID is not set!")
            id_state = "no-id"
        elif not saapi.check_broadcaster():
            self.write_console("[WARNING] SermonAudio Member ID is invalid!")
            id_state = "bad-id"
        else:
            self.id_status.configure(image=grn_status)
            id_state = "valid"

        key_state = saapi.check_key()
        if key_state == "no-key":
            self.write_console("[WARNING] SermonAudio API Key is not set!")
        elif key_state == "bad-id":
            self.write_console(
                "[WARNING] Unable to validate API key, Member ID is not valid!"
            )
        elif key_state == "invalid":
            self.write_console("[WARNING] SermonAudio API Key is invalid!")
        else:
            self.api_status.configure(image=grn_status)

        if id_state == "valid" and key_state == "valid":
            self.sa_status = True
            self.write_console(
                "[ServiceRecorder] Configuration valid, ready to record."
            )
        else:
            self.sa_status = False
        self.update_series_field()

        if not id_state == "valid" or not key_state == "valid":
            self.write_console(
                "[ServiceRecorder] Open Settings to configure ServiceRecorder."
            )

    # Functions
    def recording(self):
        self.settings_gui_button.configure(state="disabled")
        self.write_console("[ServiceRecorder] Settings disabled while recording.")
        self.file_name = f"{fullDateStamp}-{self.manualEvent.get()}"
        self.engine.is_recording = True
        Thread(target=self.engine.record_audio).start()
        self.recordButton.configure(
            text="End Recording",
            fg_color="dark red",
            hover_color="#590000",
            command=self.not_recording,
        )

    def not_recording(self):
        self.console.focus()
        self.recordButton.configure(
            text="Begin Recording",
            fg_color=("#3B8ED0", "#1F6AA5"),
            hover_color=("#36719F", "#144870"),
            command=self.recording,
        )
        if str(self.deCheck.get()) == "off":
            self.file_name = f"{self.manualDate.get()}-{self.manualEvent.get()}"
            self.manualEvent.set(f"{event_type()}")
        self.engine.sa_status = self.sa_status
        self.engine.file_name = f"{self.file_name}"
        self.engine.is_recording = False
        self.engine.full_title = f"{self.sermonField.get()}"
        self.engine.speaker_name = f"{self.speakerField.get()}"
        self.engine.bible_text = f"{self.refField.get()}"
        self.engine.series = f"{self.seriesField.get()}"
        self.engine.preach_date = (
            self.manualDate.get() if str(self.deCheck.get()) == "off" else fullDateStamp
        )
        self.engine.event_type = f"{self.manualEvent.get()}"
        if self.sa_upload.get() == 1:
            self.engine.sa_upload = f"{self.sa_upload.get()}"
        self.sermonField.delete(0, "end")
        self.speakerField.delete(0, "end")
        self.refField.delete(0, "end")
        self.seriesField.set("")
        self.settings_gui_button.configure(state="normal")

    def set_date_event(self):
        self.manualEvent.configure(
            state="normal" if str(self.deCheck.get()) == "off" else "disabled"
        )
        self.manualEvent.set(f"{event_type()}")
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

    def update_series_field(self):
        self.seriesField.configure(values=saapi.get_series_titles(), state="normal")

    def write_console(self, output):
        self.console.configure(state="normal")
        self.console.insert(customtkinter.END, f"{output}\n")
        self.console.configure(state="disabled")
        self.console.see(customtkinter.END)


def event_type():
    if dateNow.weekday() == 6:  # Sunday
        if dateNow.hour < 10 or (dateNow.hour == 10 and dateNow.minute < 30):
            event = "Sunday School"
        elif (dateNow.hour == 10 and dateNow.minute >= 30) or (dateNow.hour >= 11 and dateNow.hour < 14):
            event = "Sunday - AM"
        elif dateNow.hour >= 17:
            event = "Sunday - PM"
        else:
            event = "Special Meeting"
    elif dateNow.weekday() == 2 and dateNow.hour >= 17:  # Wednesday
        event = "Midweek Service"
    else:
        event = "Special Meeting"
    return event


if __name__ == "__main__":
    sar = RecorderGui()
    sar.validate_config()
    sar.iconbitmap(config()["GUI_ICO"])
    sar.mainloop()
