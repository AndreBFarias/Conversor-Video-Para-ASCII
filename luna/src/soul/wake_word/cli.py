from .detector import WakeWordDetector


def test_wake_word():
    import pyaudio

    print("=== Teste Wake Word (Whisper+VAD) ===")
    print("Diga o nome da entidade para testar...")

    detector = WakeWordDetector()
    if not detector.load_model():
        print("Erro: modelo nao carregado")
        return

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    print("Escutando...")
    try:
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            detected, text = detector.detect(data)
            if detected:
                print(f"DETECTADO: '{text}' -> {detector.get_greeting()}")
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
