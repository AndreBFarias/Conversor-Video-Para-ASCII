#!/usr/bin/env python3
import pyaudio

p = pyaudio.PyAudio()

print("Dispositivos que ACEITAM entrada:")
for i in range(p.get_device_count()):
    try:
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"\n[{i}] {info['name']}")
            print(f"   Default Rate: {info['defaultSampleRate']}Hz")

            # Testar 16000Hz
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=480,
                )
                stream.close()
                print("   ✓ ACEITA 16000Hz")
            except Exception as e:
                print(f"   ✗ NÃO aceita 16000Hz: {e}")
    except Exception as e:
        print(f"   Erro ao testar dispositivo: {e}")

p.terminate()
