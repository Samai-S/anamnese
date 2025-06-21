
import threading
from threading import Lock, Thread
import speech_recognition as sr

class DynamicAudioRecorder:
    def __init__(self, recognizer, mic, transcribe_callback, pause_threshold=2.0):
        self.recognizer = recognizer
        self.mic = mic
        self.transcribe_callback = transcribe_callback
        self.pause_threshold = pause_threshold

        self.is_recording = False
        self.thread = None
        self.lock = Lock()
        self.processing_threads = []

    def start(self):
        if self.is_recording:
            print("Já está gravando.")
            return

        if self.mic is None:
            raise RuntimeError("Microfone não inicializado.")

        self.is_recording = True
        self.thread = Thread(target=self._recording_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_recording = False
        if self.thread:
            self.thread.join(timeout=1.0)

        with self.lock:
            for thread in self.processing_threads:
                thread.join(timeout=1.0)
            self.processing_threads.clear()

    def _recording_loop(self):
        try:
            with self.mic as source:
                print("Ajustando ruído ambiente...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.recognizer.pause_threshold = self.pause_threshold
                self.recognizer.non_speaking_duration = 0.3

                print("Pronto para escutar.")
                while self.is_recording:
                    print("🎤 Aguardando fala...")
                    try:
                        audio = self.recognizer.listen(source)
                        print("🧠 Fala detectada! Enviando para transcrição...")

                        thread = Thread(target=self._transcribe_thread, args=(audio,), daemon=True)
                        with self.lock:
                            self.processing_threads.append(thread)
                        thread.start()
                    except Exception as e:
                        print(f"[Erro durante escuta]: {e}")
        except Exception as e:
            print(f"[Erro ao acessar o microfone]: {e}")

    def _transcribe_thread(self, audio_data):
        try:
            self.transcribe_callback(audio_data)
        except Exception as e:
            print(f"[Erro na transcrição]: {e}")
        finally:
            with self.lock:
                t = threading.current_thread()
                if t in self.processing_threads:
                    self.processing_threads.remove(t)
