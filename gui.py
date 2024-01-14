import os
import tkinter
import tkinter.messagebox
import customtkinter
import saapi
from PIL import Image, ImageTk
import time
from datetime import datetime
from saAudioEngine import AudioHandler as ah
import threading
from threading import Thread
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")
logoImg = customtkinter.CTkImage(light_image=None,dark_image=Image.open(os.getenv('GUI_LOGO')), size=(160,35))
dateNow = datetime.now()
fullDateStamp = datetime.today().strftime('%Y%m%d')


class saRecorder(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.engine = ah()
        self.deCheck = customtkinter.StringVar(value="on")
        self.fileName = "init"
        self.sermon_id = None

        # configure window
        self.title("Service Recorder")
        self.geometry(f"{660}x{580}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2,0), weight=0)
        self.grid_rowconfigure((2), weight=1)
        #self.grid_rowconfigure(1, weight=2)

        #Sidebar
        self.sidebarFrame = customtkinter.CTkFrame(self, corner_radius=0)
        self.sidebarFrame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebarFrame.columnconfigure(1, weight=1)
        self.logo = customtkinter.CTkLabel(self.sidebarFrame, image=logoImg, text="")
        self.logo.grid(row=0, column=0, pady=(25,15), columnspan=2)
        self.title_label = customtkinter.CTkLabel(self.sidebarFrame, text="Service Recorder", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=1, column=0, padx=20, pady=(0, 10), columnspan=2)
        self.recordButton = customtkinter.CTkButton(self.sidebarFrame, text="Begin Recording", command=self.recording)
        self.recordButton.grid(row=2, column=0, padx=20, pady=10, columnspan=2)
        self.saUpload = customtkinter.CTkCheckBox(self.sidebarFrame, text="Upload to SermonAudio", command=None)
        self.saUpload.grid(row=3, column=0, padx=20, pady=10, sticky="w", columnspan=2)
        self.saUpload.select()
        self.manualDateEvent = customtkinter.CTkSwitch(self.sidebarFrame, text="Automatically Set Date/Event", command=self.userSetDateEvent, onvalue="on", offvalue="off", variable=self.deCheck)
        self.manualDateEvent.grid(row=4, column=0, padx=20, pady=10, sticky="w", columnspan=2)
        self.manualEventLabel = customtkinter.CTkLabel(self.sidebarFrame, text="Event:")
        self.manualEventLabel.grid(row=5, column=0, padx=(20,10), pady=10, sticky="w")
        self.manualEvent = customtkinter.CTkOptionMenu(self.sidebarFrame, values=["Sunday AM", "Sunday PM", "Sunday School", "Midweek Service", "Special Meeting", "Camp Meeting"])
        self.manualEvent.grid(row=5, column=1, padx=(10,20), pady=10, columnspan=2, sticky="we")
        self.manualEvent.set(f"{self.eventType()}")
        self.manualEvent.configure(state="disabled")
        self.manualDateLabel = customtkinter.CTkLabel(self.sidebarFrame, text="Date:")
        self.manualDateLabel.grid(row=6, column=0, padx=(20,10), pady=10, sticky="w")
        self.manualDateLabel.configure(state="disabled")
        self.manualDate = customtkinter.CTkEntry(self.sidebarFrame, placeholder_text=f"{fullDateStamp}")
        self.manualDate.grid(row=6, column=1, padx=(10,20), pady=20, sticky="ew")
        #self.manualDate.insert(index=0,string=f"{fullDateStamp}")
        self.manualDate.configure(state="disabled")
        self.testButton = customtkinter.CTkButton(self.sidebarFrame, text="Print filename to console", command=self.printFileName)
        self.testButton.grid(row=7, column=0, padx=20, pady=10, columnspan=2)

        #Required Tags
        self.reqTagsFrame = customtkinter.CTkFrame(self)
        self.reqTagsFrame.grid(row=0,column=1,padx=10, pady=(10,0), sticky="nwes")
        self.reqTagsFrame.columnconfigure(1, weight=1)
        self.frameLabel = customtkinter.CTkLabel(self.reqTagsFrame, text="Required ID3 Tags")
        self.frameLabel.grid(row=0, column=0, padx=20, pady=(5,0), sticky="new", columnspan=2)
        self.sermonLabel = customtkinter.CTkLabel(self.reqTagsFrame,  text="Sermon Title:")
        self.sermonLabel.grid(row=1, column=0, padx=(10,0), pady=(20,0), sticky="w")
        self.sermonField = customtkinter.CTkEntry(self.reqTagsFrame,  placeholder_text="Example: The Gift of Eternal Life", width=290)
        self.sermonField.grid(row=1, column=1, padx=20, pady=(20,0), sticky="nse")
        self.speakerLabel = customtkinter.CTkLabel(self.reqTagsFrame,  text="Speaker:")
        self.speakerLabel.grid(row=2, column=0, padx=(10,0), pady=(20,0), sticky="w")
        self.speakerField = customtkinter.CTkEntry(self.reqTagsFrame,  placeholder_text="Example: Johnny Clardy", width=290)
        self.speakerField.grid(row=2, column=1, padx=(20), pady=(20,0), sticky="nse")
        self.refLabel = customtkinter.CTkLabel(self.reqTagsFrame,  text="Text Reference:")
        self.refLabel.grid(row=3, column=0, padx=(10,0), pady=(20,20), sticky="w")
        self.refField = customtkinter.CTkEntry(self.reqTagsFrame,  placeholder_text="Example: 2 Corinthians 9", width=290)
        self.refField.grid(row=3, column=1, padx=20, pady=(20,20), sticky="nse")

        #Optional Tags
        self.optTagsFrame = customtkinter.CTkFrame(self)
        self.optTagsFrame.grid(row=1,column=1,padx=10, pady=(10,0), sticky="nwe")
        self.optTagsFrame.columnconfigure(1, weight=1)
        self.frameLabel = customtkinter.CTkLabel(self.optTagsFrame,  text="Optional ID3 Tags")
        self.frameLabel.grid(row=0, column=0, padx=20, pady=(5,0), sticky="new", columnspan=2)
        self.seriesLabel = customtkinter.CTkLabel(self.optTagsFrame,  text="Series Title:")
        self.seriesLabel.grid(row=1, column=0, padx=(10,0), pady=(20,20), sticky="w")
        self.seriesField = customtkinter.CTkComboBox(self.optTagsFrame, width=290, values=saapi.getAllSeries())
        self.seriesField.set("")
        self.seriesField.grid(row=1, column=1, padx=20, pady=(20,20), sticky="nse")

    #Functions
    def recording(self):
        print("Recording started.")
        self.fileName = f"{fullDateStamp}-{self.manualEvent.get()}_{self.timeStamp()}"
        self.engine.is_recording = True
        Thread(target=self.engine.newRecordAudio).start()
        self.recordButton.configure(text="End Recording", fg_color="dark red", hover_color="#590000", command=self.notRecording)
        

    def notRecording(self):
            print("Recording ended.")
            self.recordButton.configure(text="Begin Recording", fg_color=('#3B8ED0', '#1F6AA5'), hover_color=("#36719F", "#144870"), command=self.recording) 
            if str(self.deCheck.get()) == "off":
                self.fileName = f"{self.manualDate.get()}-{self.manualEvent.get()}_{self.timeStamp()}"
            self.engine.fileName = f"{self.fileName}"
            self.engine.is_recording = False
            self.engine.fullTitle = f"{self.sermonField.get()}"
            self.engine.speakerName = f"{self.speakerField.get()}"
            self.engine.bibleText = f"{self.refField.get()}"
            self.engine.series = f"{self.seriesField.get()}"
            self.engine.publishTimestamp = (int(time.time()) + 300)
            self.engine.preachDate = self.manualDate.get() if str(self.deCheck.get()) == "off" else fullDateStamp
            self.engine.eventType = f"{self.manualEvent.get()}"
            self.engine.newSaveAudio()
            #if self.saUpload.get():
            #    self.engine.saUpload = 1
            #    self.engine.createSermon()
            #else:
            #     self.engine.saUpload = 0     
          
    def userSetDateEvent(self):
            self.manualEvent.configure(state="normal" if str(self.deCheck.get()) == "off" else "disabled")
            self.manualDate.configure(state="normal" if str(self.deCheck.get()) == "off" else "disabled")

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
         return datetime.now().timestamp()
    
    def checkSeries(self):
         pass

if __name__ == "__main__":
    sar = saRecorder()
    sar.iconbitmap(os.getenv('GUI_ICO'))
    sar.mainloop()