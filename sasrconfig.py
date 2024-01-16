import os
import json

def config(**kwargs):
    config_path = "config.json"
    _config_initialize(config_path=config_path)

    with open(config_path, "r") as config_file:
        config_data = json.load(config_file)
        if kwargs:
            config_data.update(kwargs)
    with open(config_path, "w") as config_file:
        config_file.write(json.dumps(config_data, indent=2))
    return config_data


def _config_initialize(config_path):
    if not os.path.isfile(config_path):
        initial = {
            "APPEND_TIMESTAMP": "FALSE",
            "BROADCASTER_ID": "",
            "SA_API_KEY": "",
            "GUI_LOGO": "img/logo.png",
            "GUI_ICO": "img/icon.ico",
            "AUDIO_PATH": "recordings"

        }
        with open(config_path, "w") as config_file:
            config_file.write(json.dumps(initial))