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
After you've populated the settings window with the appropriate values, close the program and reopen it with the
`python gui.py` command. You're now ready to press `Begin Recording`! If you're uploading to SermonAudio, make sure to populate the
`Sermon Title` and `Speaker` fields **BEFORE ENDING THE RECORDING**. No, `Text Reference` isn't required and will be
moving down to the optional section soon. If the `Event` and `Date` fields on the left sidebar aren't the desired
values, turn off `Automatically Set Date/Event` and choose the desired settings. Make sure to enter your date in
the `YYYYMMDD` format. Once you're done, click `End Recording`, and Service Recorder will take care of the rest!
<br><br>
*Note: Keep an eye on the console window, it prints some useful information about the audio file and upload process!*
