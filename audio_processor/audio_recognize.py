import whisper # keep if you use it
import os
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
import json # Moved import to top
from faster_whisper import WhisperModel
from io import BytesIO





MODEL_EXPECTED_SR = 16000 # The vosk-model-small-pt-0.3 expects 16kHz
try:
    model_path = r"c:\Users\Samai\Desktop\anamnese\vosk-model-small-pt-0.3"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Vosk model path not found: {model_path}")
    vosk_model = Model(model_path)
    print("Modelo Vosk carregado com sucesso.")
except Exception as e:
    print(f"Erro ao carregar modelo Vosk: {e}")
    vosk_model = None # Set to None so we can check later


def recognize_google(recognizer_instance, audio_data):
    try:
        return recognizer_instance.recognize_google(audio_data, language="pt-BR")
    except sr.UnknownValueError:
        print("Google: Não foi possível entender o áudio.")
        return ""
    except sr.RequestError as e:
        print(f"Google: Erro de requisição; {e}")
        return ""

def recognize_vosk(recognizer_instance, audio_data_sr): # audio_data_sr is SpeechRecognition AudioData
    global vosk_model, MODEL_EXPECTED_SR
    if not vosk_model:
        print("Modelo Vosk não está carregado. Não é possível transcrever.")
        return ""

    # --- MODIFICATION 2: Handle Sample Rate for Vosk ---
    # Vosk KaldiRecognizer needs raw audio data at the model's expected sample rate (16kHz)
    # audio_data_sr is a speech_recognition.AudioData object.
    # Its audio_data_sr.sample_rate might not be 16000 Hz.
    
    print(f"Vosk: Recebido AudioData com SR: {audio_data_sr.sample_rate}Hz, SW: {audio_data_sr.sample_width} bytes")

    data_to_process = audio_data_sr.get_raw_data()
    current_sample_rate = audio_data_sr.sample_rate

    # Resample if necessary using pydub (add pydub to your requirements: pip install pydub)
    # This is more robust if sr.Microphone(sample_rate=16000) doesn't work as expected.
    if current_sample_rate != MODEL_EXPECTED_SR:
        print(f"Vosk: Resampling de {current_sample_rate}Hz para {MODEL_EXPECTED_SR}Hz...")
        try:
            from pydub import AudioSegment
            import io
            
            # Create AudioSegment from raw data
            audio_segment = AudioSegment(
                data=data_to_process,
                sample_width=audio_data_sr.sample_width,
                frame_rate=current_sample_rate,
                channels=1  # Assuming mono, which speech_recognition usually gives
            )
            
            # Resample
            audio_segment = audio_segment.set_frame_rate(MODEL_EXPECTED_SR)
            
            # Get raw data from resampled segment
            data_to_process = audio_segment.raw_data
            print(f"Vosk: Resampling concluído. Novo tamanho dos dados: {len(data_to_process)}")
        except ImportError:
            print("Vosk: pydub não instalado. Não é possível resamplear. Tente 'pip install pydub'.")
            print("Vosk: Continuando com a taxa de amostragem original, pode falhar.")
            # If pydub is not available, we can't resample here easily without more complex code
            # And KaldiRecognizer will likely fail or produce garbage.
            # For now, we will let it proceed, but it's unlikely to work well.
        except Exception as e:
            print(f"Vosk: Erro durante o resampling com pydub: {e}")
            return "" # Abort if resampling fails critically


    # Initialize KaldiRecognizer with the MODEL'S expected sample rate.
    # The data fed to AcceptWaveform MUST match this rate.
    recognizer = KaldiRecognizer(vosk_model, MODEL_EXPECTED_SR)
    recognizer.SetWords(True) # Optional: if you want word-level timestamps

    # Process the (potentially resampled) audio data
    # For a single block of audio:
    if recognizer.AcceptWaveform(data_to_process):
        result_json_str = recognizer.Result()
    else:
        result_json_str = recognizer.FinalResult() # Use FinalResult to get everything processed
    # --- END MODIFICATION 2 ---

    print("Resultado bruto do Vosk:", result_json_str) # This print is crucial!
    
    try:
        result_dict = json.loads(result_json_str)
        return result_dict.get("text", "") # Use .get for safety if "text" key is missing
    except json.JSONDecodeError:
        print(f"Vosk: Não foi possível decodificar o JSON: {result_json_str}")
        if '"text" : ""' in result_json_str: # Vosk sometimes returns this for silence/unrecognized
             return ""
        return f"Erro JSON Vosk: {result_json_str[:100]}" # Return part of the error if not empty
    except Exception as e:
        print(f"Vosk: Erro ao processar resultado JSON: {e}")
        return ""


def recognize_whisper_from_memory(audio_data_sr):
   
    try:
        # Inicializar modelo
        model_size = "large-v3"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        # Obter dados brutos do áudio
        raw_data = audio_data_sr.get_wav_data()
        
        # Usar BytesIO como arquivo em memória
        audio_buffer = BytesIO(raw_data)
        
        # Transcrever
        print("Whisper: iniciando transcrição...")
        segments, info = model.transcribe(audio_buffer, beam_size=5, language="pt")
        
        # Juntar os textos dos segmentos
        texto = " ".join(segment.text.strip() for segment in segments)
        return texto

    except Exception as e:
        print(f"Whisper: Erro durante a transcrição - {e}")
        return ""
