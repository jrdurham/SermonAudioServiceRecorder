# SermonAudio Service Recorder

<center><img src=https://i.imgur.com/hKfOBGA.png)></center>
<br>

Service Recorder utilizes the [SermonAudio Python Module](https://pypi.org/project/sermonaudio/) and 
[CustomTkinter](https://customtkinter.tomschimansky.com/) to assist in recording sermons and automate the process of uploading them to SermonAudio.

## What Service Recorder Does

1. Records your sermon from the selected audio input.
1. Applies a 5 second fade to the beginning and end of the audio.
1. Exports the resulting audio to an MP3 file in a directory of your choosing.
1. Saves the relevant fields to the MP3 file's ID3 tag fields used by SermonAudio, just in case you'd rather upload manually 
via ftp or Dropbox.  
*Note: For debugging purposes, current behavior appends a timestamp to the file name, for example:
`20240115-Sunday - AM_1705374455.mp3`. Remove the `_ 1705374455` section of the file name before uploading via other
semi-automated means. There is no need to remove the timestamp if you're uploading to SermonAudio via the website.*
1. Creates a sermon with the information entered before pressing `End Recording`, then uploads the MP3 file to the sermon.

## What Sermon Recorder Does *NOT* Do

1. Handle errors and exceptions very well. This was thrown together over the course of a weekend. I am a novice python developer, 
so trying to utilize it outside of the expected behavior won't work well. I hope to introduce better error handling in the future. The biggest
thing to watch out for is that all three fields in the `Required ID3 Tags` section are filled out _prior_ to ending the recording.
If you have `Upload to SermonAudio` checked (default behavior), pressing `End Recording` kicks off the upload process.
If it fails, you'll have to upload the message manually via the website. Keep an eye on the console window, it *does* print
enough information to inform you of what's happening during the entire process.
1. Attach a sermon to a series on SermonAudio. This is the next thing in my TODO list. In the meantime, you can add a sermon
to a series manually.  
<br>  
If neither of these two things deter you, proceed!

## Installation
1. Install Python 3.12+, if you haven't already.  
1. This repo requires FFMPEG. Make sure to install it from a trusted source (I recommend taking a look at the [gyan page](https://www.gyan.dev/ffmpeg/builds/).
There, you will find the easy ways to install FFMPEG like `winget`, as well as the release builds for download.)
1. From the repo's directory, run `pip install -r requirements.txt`.  

## Running Service Recorder
To run the GUI, it's as simple as running `python gui.py` from within the root directory of the repo.

When you first run Service Recorder, click `Settings` in the lower left hand side of the window, and populate
the fields with the appropriate settings.
<br><br>
Login to [SermonAudio's members only area](https://www.sermonaudio.com/members), and make note of the `Member ID` and the `API Key`.
In the settings menu of Service Recorder, paste the `Member ID` and `API Key` into their appropriate fields.
<br><br>
Next, you can select the `Audio Device` to record from. If you're unsure which device to use, Service Recorder uses
the machine's default audio device, so it's probably fine to leave this as is, only change it if you run into issues.
The final field, `Audio File Path`, allows you to choose where Service Recorder saves the resulting MP3 files.
<br><br>
After you've populated the settings window with the appropriate values, you're now ready to press `Begin Recording`! If you're uploading to SermonAudio, make sure to populate the
`Sermon Title` and `Speaker` fields **BEFORE ENDING THE RECORDING**. No, `Text Reference` isn't required and will be
moving down to the optional section soon. If the `Event` and `Date` fields on the left sidebar aren't the desired
values, turn off `Automatically Set Date/Event` and choose the desired settings. Make sure to enter your date in
the `YYYYMMDD` format. Once you're done, click `End Recording`, and Service Recorder will take care of the rest!
<br><br>
*Note: Keep an eye on the console window, it prints some useful information about the audio file and upload process!*

## Useful Information  
<br>

### Automatic Event Logic
By default, Service Recorder sets the event type automatically to one of three event types for SermonAudio's upload.
based on when the recording is started. The logic works as follows:  
<br>
Event Type: `Sunday School`  
Criteria: Recording started on Sunday *before* 1100.  
<br>
Event Type: `Sunday - AM` (Main Sunday morning service)  
Criteria: Recording started on Sunday *after* 1100, but before 1400.  
<br>
Event Type: `Sunday PM`  
Criteria: Recording started on Sunday *after* 1700  
<br>
Event Type: `Midweek Service`  (Wednesday evening)  
Criteria: Recording started on Wednesday *after* 1700.  
<br>

A few more options are available via the dropdown menu if you deselect `Automatically Set Date/Event`, to allow easy use
during special services like Camp Meetings and Revivals. Not all of the SermonAudio event types are listed here, 
as a matter of fact, most of them are *not*, however I do plan to add them in the
future.  
<br>

### SermonAudio Publish Time
Uploaded sermons are set to publish 5 minutes after the sermon is created.
This is to allow a short window to correct any information that might've been entered incorrectly in the GUI
or make any changes to the sermon on SermonAudio's website before it goes public.  
<br>

### Extra Config Options
When the GUI is first run, it will create a file named "config.json" in the repo directory.
Currently, there are three extra options that can be manually set there:  
<br>

`APPEND_TIMESTAMP` - Default setting:  `FALSE`  
If you change this setting to `TRUE`, a unix timestamp will be appended to the filename at export.
this is useful when testing and multiple files are being generated that might have the same filename
with the GUI's default filenaming behaviors.
<br>

`GUI_LOGO` - Default setting: `img/logo.png`  
This is an image file that is displayed in the GUI above the 'Service Recorder' text.
A blank image file is included with the repo, it can be edited directly, replaced, or you can specify a path
to an image with this option. If you'd like to do this, the image size in GUI is 160x35.
Your image can be larger, but needs to match the 32:7 ratio of the original image to display without
distortion. I added this option to show my church's logo in the GUI.  
<br>

`GUI_ICO` - Default setting: `img/icon.ico`  
This is a .ico file that is displayed next to the window title. If you want to replace it, use an icon file
with a 1:1 aspect ratio, up to a dimension of 256x256.  
<br>

In addition to these three options, you can also set the options that are configurable via the
GUI here as well, although the `DEVICE_NAME` setting needs to match the exact option from the GUI, so it's
best to not manually edit this option via config.json.
