import speech_recognition as sr
from faster_whisper import WhisperModel
from io import BytesIO



def recognize_google(recognizer_instance, audio_data):
    try:
        return recognizer_instance.recognize_google(audio_data, language="pt-BR")
    except sr.UnknownValueError:
        print("Google: Não foi possível entender o áudio.")
        return ""
    except sr.RequestError as e:
        print(f"Google: Erro de requisição; {e}")
        return ""


def recognize_whisper_from_memory(audio_data_sr):
   
    try:
        model_size = "large-v3"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        raw_data = audio_data_sr.get_wav_data()
        
        audio_buffer = BytesIO(raw_data)
        
        print("Whisper: iniciando transcrição...")
        segments, info = model.transcribe(audio_buffer, beam_size=5, language="pt")
        
        texto = " ".join(segment.text.strip() for segment in segments)
        return texto

    except Exception as e:
        print(f"Whisper: Erro durante a transcrição - {e}")
        return ""
