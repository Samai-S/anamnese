# audio_processor/multi_recognizer.py
import threading

from audio_processor import audio_recognize

class MultiRecognizer:
    def __init__(self, recognizer_instance_sr): 
        self.recognizer_sr = recognizer_instance_sr
        self.results = {}
        self.lock = threading.Lock() 
        self.threads = []

    def _thread_wrapper(self, name, func, *args):
        def wrapper():
            result = "" 
            try:
                result = func(*args)
            except Exception as e:
                result = f"Erro em {name}: {str(e)}"
            with self.lock:
                self.results[name] = result
        return wrapper

    def transcribe_all(self, audio_data):
        self.results.clear() # Clear results for this specific chunk
        self.threads.clear()

        transcribers = {
            "google": self._thread_wrapper("google", audio_recognize.recognize_google, self.recognizer_sr, audio_data),
            "whisper": self._thread_wrapper("whisper", audio_recognize.recognize_whisper_from_memory, audio_recognize._whisper_model, audio_data),
        }

        for name, func_wrapper in transcribers.items():
            thread = threading.Thread(target=func_wrapper)
            thread.start()
            self.threads.append(thread)

        for thread in self.threads:
            thread.join() # Wait for both recognizers to finish for this audio_data chunk

        # Return a copy of the results to avoid issues if self.results is cleared elsewhere quickly
        with self.lock:
            return self.results.copy()