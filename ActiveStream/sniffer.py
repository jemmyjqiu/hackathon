import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

print("\n--- AVAILABLE AUDIO DEVICES ---")
for i in range(0, numdevices):
    if (p.get_device_info_by_index(i).get('maxInputChannels')) > 0:
        print(f"ID {i}: {p.get_device_info_by_index(i).get('name')}")

p.terminate()