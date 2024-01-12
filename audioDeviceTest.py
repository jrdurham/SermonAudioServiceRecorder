import sounddevice as sd


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
        print(f"Dev ID: {dev}\nDev Name: {hostDev['name']}")

#for i in range(p.get_device_count()):
#    info = p.get_device_info_by_index(i)
#    if "Headset Microphone" in info["name"] and info["hostApi"] == api:
#        print(f"Device Name: {info['name']}\nDevice Index: {info['index']}")