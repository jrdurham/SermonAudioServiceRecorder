# <p align="center">SA Service Recorder</p>

<p align="center"><img src=https://i.imgur.com/Swdh9Ah.png)></p>
<br>

### <p align="center">Service Recorder assists in recording audio during church services<br>and automating the process of uploading them to SermonAudio.</p>

## What Service Recorder Does

1. Records your sermon from the selected audio input.
1. Applies a 5-second fade to the beginning and end of the audio.
1. Exports the resulting audio to an MP3 file in a directory of your choosing.
1. Saves the relevant fields to the MP3 file's ID3 tag fields used by SermonAudio, just in case you'd rather upload manually 
via SermonAudio's ftp or Dropbox options.
1. Creates a SermonAudio entry with the information entered before pressing `End Recording`, then uploads the MP3 file to the sermon.

## What Service Recorder Does *NOT* Do
Handle errors and exceptions very well. This was thrown together over the course of a weekend. I am a novice python developer,
so I have a lot to learn about properly handling exceptions. Due to this, trying to utilize Service Recorder
outside the expected behavior won't work well. I hope to introduce better error handling in the future. The biggest
thing to watch out for is that all three fields in the `Required ID3 Tags` section are filled out _prior_ to ending the recording.
If you have `Upload to SermonAudio` checked (default behavior), pressing `End Recording` kicks off the upload process.
If it fails, you'll have to go to the recordings folder and upload the file manually via the website. Keep an eye on the
console window, it *does* print enough information to inform you of what's happening during the entire process.
<br>  
If this doesn't deter you, proceed!

## Installation
1. Install Python 3.12+, if you haven't already. I highly recommend installing using the installer from [Python's Website](https://www.python.org/downloads/), and NOT the Windows Store app.  
1. This repo requires FFMPEG. Make sure to install it from a trusted source (I recommend taking a look at the [gyan page](https://www.gyan.dev/ffmpeg/builds/).
There, you will find the easy ways to install FFMPEG like `winget` and even python's `pip` package manager,
as well as the release builds for download.)
    1. If you're using Windows, my preferred method is to use the
[Chocolatey Package Manager](https://chocolatey.org/install). Once you have Chocolatey installed, installing FFMPEG is
as simple as running `choco install ffmpeg` from an elevated (`Run As Admin`) powershell prompt.
1. From the repo's directory, run `pip install -r requirements.txt`.  

## Running Service Recorder
To run the GUI, it's as simple as running `python gui.py` from within the root directory of the repo.

When you first run Service Recorder, click `Settings` in the lower left hand side of the window. Login to
[SermonAudio's members only area](https://www.sermonaudio.com/members), and make note of the `Member ID` and `API Key` values.
In the settings menu, paste the `Member ID` and `API Key` into their appropriate fields.
<br><br>
Next, you can select the `Audio Device` to record from. If you're unsure which device to use, Service Recorder uses
the machine's default audio device. It's probably fine to leave this as is, only change it if you know what
you're doing, or you run into issues.
The final field, `Audio File Path`, allows you to choose where Service Recorder saves the resulting MP3 files.
<br><br>
After you've populated the settings window with the appropriate values, you're now ready to press `Begin Recording`!
If you're uploading to SermonAudio, make sure to populate the `Sermon Title` and `Speaker` fields
**BEFORE ENDING THE RECORDING**. If the `Event` and `Date` fields on the left sidebar aren't the desired
values, turn off `Automatically Set Date/Event` and choose the desired settings. Make sure to enter your date in
`YYYYMMDD` format. Once you're done, click `End Recording`, and Service Recorder will take care of the rest!
<br><br>
*Note: Keep an eye on the console window, it prints some useful information about the audio file and upload process!*

## Useful Information

### Automatic Event Logic
By default, Service Recorder sets the event type automatically to one of three event types for SermonAudio's upload,
based on when the recording is started. The logic works as follows:  
<br>
Event Type: `Sunday School`  
Criteria: Recording started on Sunday *before* 1030.  
<br>
Event Type: `Sunday - AM` (Main Sunday morning service)  
Criteria: Recording started on Sunday *at or after* 1030, but *before* 1400.  
<br>
Event Type: `Sunday PM`  
Criteria: Recording started on Sunday *after* 1700  
<br>
Event Type: `Midweek Service`  (Wednesday evening)  
Criteria: Recording started on Wednesday *after* 1700.  
<br>

A few more options are available via the dropdown menu if you deselect `Automatically Set Date/Event`, to facilitate
ease of use during special services like Camp Meetings and Revivals. Not all SermonAudio event types are listed
here (as a matter of fact, most of them are *not*), however I do plan to add them in the future.  
<br>

### SermonAudio Publish Time
Uploaded sermons are set to publish 5 minutes after the sermon is created.
This is to allow a short window to correct any information that might've been entered incorrectly in the GUI
or make any changes to the sermon on SermonAudio's website before it goes public.  
<br>

### Extra Config Options
When the GUI is first run, it will create a file named "config.json" in the repo directory where it stores information
entered into the settings window. There are a few extra options that can be manually set in the file:  
<br>

`APPEND_TIMESTAMP` - Default setting:  `FALSE`  
If you change this setting to `TRUE`, a unix timestamp will be appended to the filename at export.
This is useful when testing and multiple files are being generated that might have the same filename
when set via the GUI's default file naming behaviors.

`GUI_LOGO` - Default setting: `img/logo.png`  
This is an image file that is displayed in the GUI above the 'Service Recorder' text.
A blank image file is included with the repo. It can be edited directly, replaced, or you can specify a path
to an image with this option. If you'd like to do this, the image size in GUI is 160x35.
Your image can be larger, but needs to match the 32:7 ratio of the original image to display without
distortion. I added this option to show my church's logo.  


`GUI_ICO` - Default setting: `img/icon.ico`  
This is an .ico file that is displayed next to the window title. If you want to replace it, use an icon file
with a 1:1 aspect ratio, up to a dimension of 256x256.  


`FIRST_RUN` - Default setting: `true`
This flag represents a boolean that is intended to do a few things on the first run of the program. It currently doesn't
It currently doesn't do anything, I'm on the fence about whether to utilize it or not now that I've added configuration
validation, and likely will be removed in the future.

In addition to these options, you can set the options that are configurable via the
GUI here as well. If you do so, keep in mind the `DEVICE_NAME` setting needs to match the exact option from the GUI,
so it's best to only use the settings window to edit this option.

## Notes
This program is written in python and mainly utilizes the following python modules:  
<br>
[customtkinter](https://pypi.org/project/customtkinter/) - UI library used to build the GUI  
[sounddevice](https://pypi.org/project/sounddevice/) - Interfacing with audio input and recording audio streams  
[soundfile](https://pypi.org/project/soundfile/) -  Interfacing with the audio file during recording  
[pydub](https://pypi.org/project/pydub/) - Manipulating the recorded audio and saving to the final MP3 file  
[sermonaudio](https://pypi.org/project/sermonaudio/) - Interfacing with SermonAudio via their API

