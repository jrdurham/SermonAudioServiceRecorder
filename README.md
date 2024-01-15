# SermonAudio Service Recorder

A GUI that records audio and uploads it to SermonAudio with the selected parameters.

## Installation
1. Install Python 3.12+, if you haven't already.  
1. This repo requires FFMPEG. Make sure to install it from a trusted source.  
1. From the repo's directory, run `pip install -r requirements.txt`.  

## Configuration
Create a text file named `.env` in the root of the repo's directory, and fill it with the following values, replacing `<value>` for each with the appropriate information:  
1. `SA_API_KEY=<value>`  
   1. This is your SermonAudio API key. It's available in the Member Area.  
1. `GUI_Logo=<value>`  
   1. File path to an logo image.  
1. Required, but will be optional in the future.  
   1. `GUI_ICO=<value>`  
1. File path to an icon, preferably 256x256 to use for the GUI's icon.
   1. Required, but will be optional in the future.  
1. `AUDIO_DIR=<value>`  
   1. This is the folder you want the audio files saved to when recording is complete.  

## Running SermonAudio Service Recorder
To run the GUI, it's as simple as running 'python gui.py' from within the root directory of the repo.
