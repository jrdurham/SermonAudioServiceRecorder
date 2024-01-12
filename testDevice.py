#for fmt in [pyaudio.paInt8, pyaudio.paInt16, pyaudio.paInt24, pyaudio.paInt32, pyaudio.paFloat32]:
#            supported = p.is_format_supported(rate=44100, input_device=24, input_format=fmt, input_channels=1)
#            if supported:
#                print(f"Supported Format: {p.get_format_from_width(p.get_sample_size(fmt))} ({fmt})")
#            else:
#                print(f"Not Supported: {p.get_format_from_width(p.get_sample_size(fmt))} ({fmt})")

import pyaudio

p = pyaudio.PyAudio()

device_info = p.get_device_info_by_index(24)

print(f"Device Name: {device_info['name']}")
print(f"Device Index: {device_info['index']}")

highest_supported_format = None
max_sample_size = 0

for fmt in [pyaudio.paInt8, pyaudio.paInt16, pyaudio.paInt24, pyaudio.paInt32, pyaudio.paFloat32]:
    supported = p.is_format_supported(rate=44100, input_device=device_info['index'], input_format=fmt, input_channels=1)

    if supported:
        sample_size = p.get_sample_size(fmt)
        if sample_size > max_sample_size:
            max_sample_size = sample_size
            highest_supported_format = fmt
            format_str = p.get_format_from_width(p.get_sample_size(fmt))

if highest_supported_format is not None:
    print(f"Highest Supported Format: {format_str} {p.get_format_from_width(max_sample_size)} ({highest_supported_format})")
else:
    print("No supported format found.")
