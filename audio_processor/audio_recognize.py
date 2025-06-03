# audio_processor/audio_recognizer.py
import speech_recognition as sr
from faster_whisper import WhisperModel
from io import BytesIO
import re

WHISPER_MODEL_SIZE = "turbo"  
print(f"Loading Whisper model ({WHISPER_MODEL_SIZE})... This may take a moment.")

try:
    _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    print("Whisper model loaded.")
except Exception as e:
    _whisper_model = None
    print(f"Error loading Whisper model: {e}. Whisper transcription will not be available.")

def remove_palavras_repetidas(texto):
    if not texto:
        return ""
    return re.sub(r'\b(\w+)( \1\b)+', r'\1', texto, flags=re.IGNORECASE)

def recognize_google(recognizer_instance, audio_data):
    try:
        # print("Google: Transcribing...")
        texto = recognizer_instance.recognize_google(audio_data, language="pt-BR")
        return remove_palavras_repetidas(texto)
    except sr.UnknownValueError:
        # print("Google: Não foi possível entender o áudio.")
        return ""
    except sr.RequestError as e:
        print(f"Google: Erro de requisição; {e}")
        return ""

def recognize_whisper_from_memory(model_instance, audio_data_sr): 
    print("\nrecognize_whisper accessed")
    if model_instance:
        return "Whisper model not available."
    try:
        print("Whisper: Transcribing...")
        raw_data = audio_data_sr.get_wav_data()
        audio_buffer = BytesIO(raw_data)

        segments_gen, info = model_instance.transcribe(
            audio_buffer,
            beam_size=5,
            language="pt",
            condition_on_previous_text=True
        )

        segments = list(segments_gen)
        print(f"Whisper: {len(segments)} segmento(s) reconhecido(s).")

        for i, s in enumerate(segments):
            print(f"  [{i}] Segment: '{s.text}'")

        texto = " ".join(segment.text.strip() for segment in segments)
        return remove_palavras_repetidas(texto)
    except Exception as e:
        print(f"Whisper: Erro durante a transcrição - {e}")
        return ""



# The old transcrever_com_varios_modelos can be removed or kept if used elsewhere
# It's not directly used by the new real-time audio_handler