import speech_recognition as sr
from tkinter import messagebox
from threading import Thread
# from file_handler import output_text # Assuming you'll uncomment later
# from audio_processor import audio_recognize # Using directly from global space now
from audio_processor import audio_recognize # Import directly

r = sr.Recognizer()
# --- MODIFICATION 1: Attempt to set microphone sample rate ---
TARGET_SAMPLE_RATE = 16000 # For Vosk model
try:
    mic = sr.Microphone(sample_rate=TARGET_SAMPLE_RATE)
    print(f"Microphone initialized with sample_rate={mic.SAMPLE_RATE}Hz (target: {TARGET_SAMPLE_RATE}Hz)")
    if mic.SAMPLE_RATE != TARGET_SAMPLE_RATE:
        print(f"WARNING: Microphone did not accept target sample rate. Actual rate: {mic.SAMPLE_RATE}Hz. "
              "Recognition quality with Vosk may be affected unless resampling is performed.")
except Exception as e:
    print(f"Could not initialize microphone with target sample rate {TARGET_SAMPLE_RATE}Hz. Using default. Error: {e}")
    mic = sr.Microphone()
    print(f"Microphone initialized with default sample_rate={mic.SAMPLE_RATE}Hz")

# --- END MODIFICATION 1 ---

stop_listening = None
is_recording = False
audio_chunks = []
processing_thread = None

def audio_callback(recognizer, audio):
    global audio_chunks
    if is_recording:
        #print("Chunk recebido...")
        audio_chunks.append(audio.get_raw_data())

def start_recording(root, status_label, start_button, stop_button):
    global stop_listening, is_recording, audio_chunks
    if is_recording:
        print("Já está gravando!")
        return

    audio_chunks = []
    status_label.config(text="Ajustando para ruído ambiente...")
    root.update_idletasks()

    try:
        with mic as source:
            print(f"Adjusting for ambient noise. Mic SR: {source.SAMPLE_RATE}, SW: {source.SAMPLE_WIDTH}")
            r.adjust_for_ambient_noise(source, duration=0.7)
        stop_listening = r.listen_in_background(mic, audio_callback, phrase_time_limit=None) # phrase_time_limit=None to ensure continuous stream if needed
        is_recording = True
        print("Gravando...")
        status_label.config(text="Gravando... Fale agora!")
        start_button.config(state="disabled", bg="gray")
        stop_button.config(state="normal", bg="red")
    except Exception as e:
        messagebox.showerror("Erro de Microfone", f"Não foi possível iniciar a gravação:\n{e}")
        status_label.config(text="Erro ao iniciar. Verifique o microfone.")

def stop_recording_func(root, status_label, start_button, stop_button):
    global stop_listening, is_recording, processing_thread
    if not is_recording:
        print("Não está gravando.")
        return

    print("Parando gravação...")
    status_label.config(text="Parando gravação...")
    root.update_idletasks()

    if stop_listening:
        stop_listening(wait_for_stop=False) # Set wait_for_stop to False is good for responsiveness
        stop_listening = None

    is_recording = False # Set this immediately
    start_button.config(state="normal", bg="green")
    stop_button.config(state="disabled", bg="gray") # Disable stop until processing finishes? or re-enable after process

    if audio_chunks:
        status_label.config(text="Processando áudio...")
        # Pass buttons to re-enable them after processing in process_audio_data
        processing_thread = Thread(target=lambda: process_audio_data(status_label, start_button, stop_button))
        processing_thread.start()
    else:
        print("Nenhum áudio gravado.")
        status_label.config(text="Nenhum áudio gravado.")
        # Re-enable start button if no audio
        start_button.config(state="normal", bg="green")

def process_audio_data(status_label, start_button, stop_button): # Added buttons for state management
    global audio_chunks, r # r is needed by recognizers
    print("Iniciando reconhecimento...")

    try:
        # Use the actual sample rate and width from the microphone object
        # These were set (or defaulted) when 'mic' was initialized
        actual_sample_rate = mic.SAMPLE_RATE
        actual_sample_width = mic.SAMPLE_WIDTH
        print(f"Processing audio with: SR={actual_sample_rate}Hz, SW={actual_sample_width}")

    except AttributeError:
        print("Warning: mic.SAMPLE_RATE or mic.SAMPLE_WIDTH not found. Using defaults (44100, 2). This might be problematic.")
        actual_sample_rate = 44100  # Fallback, but less ideal
        actual_sample_width = 2    # Fallback (2 bytes = 16-bit)

    if not audio_chunks:
        print("Sem áudio para processar.")
        status_label.config(text="Erro: Sem dados de áudio.")
        start_button.config(state="normal", bg="green") # Re-enable start button
        stop_button.config(state="disabled", bg="gray")
        return

    combined_data = b"".join(audio_chunks)
    audio_chunks.clear() # Clear chunks *before* potentially long processing

    # Create AudioData with the *actual* captured sample rate and width
    combined_audio = sr.AudioData(combined_data, actual_sample_rate, actual_sample_width)

    try:
        text = ""
        # text = recognize_google(r, combined_audio)
        text = audio_recognize.recognize_vosk(r, combined_audio) # Pass the combined_audio directly
        #text = audio_recognize.recognize_whisper_from_memory(combined_audio)

        if text:
            print("Texto reconhecido:", text)
            # output_text(text) # Assuming you'll uncomment later
            status_label.config(text=f"Pronto. (Texto salvo)") # Indicate success
            messagebox.showinfo("Transcrição", f"Texto reconhecido:\n\n{text}")
        else:
            print("Texto reconhecido está VAZIO.")
            status_label.config(text="Não foi possível entender o áudio (resultado vazio).")

    except sr.UnknownValueError:
        print("Vosk/Google não pôde entender o áudio.")
        status_label.config(text="Não foi possível entender o áudio.")
        messagebox.showwarning("Transcrição Falhou", "Não foi possível entender o áudio.")
    except sr.RequestError as e:
        print(f"Erro de API/Rede: {e}")
        messagebox.showerror("Erro de Rede", f"Erro ao conectar ao serviço de reconhecimento:\n{e}")
        status_label.config(text="Erro de rede no reconhecimento.")
    except Exception as e:
        print(f"Erro durante o reconhecimento: {e}")
        status_label.config(text=f"Erro no processamento: {e}")
        messagebox.showerror("Erro", f"Ocorreu um erro durante o processamento:\n{e}")
    finally:
        # audio_chunks.clear() # Moved clear earlier
        # Re-enable buttons regardless of outcome
        start_button.config(state="normal", bg="green")
        stop_button.config(state="disabled", bg="gray")
        status_label.config(text="Pronto para gravar") # Reset status

def on_closing(root):
    global stop_listening, is_recording, processing_thread
    print("Fechando aplicação...")
    if is_recording and stop_listening:
        print("Parando gravação em andamento...")
        stop_listening(wait_for_stop=False)
        is_recording = False # Ensure this is set

    if processing_thread and processing_thread.is_alive():
        print("Aguardando processamento de áudio terminar...")
        # status_label.config(text="Finalizando...") # status_label might not exist if root is gone
        processing_thread.join(timeout=5.0) # Wait for a bit
        if processing_thread.is_alive():
            print("Processamento ainda em execução após timeout. Forçando saída.")

    print("Destruindo janela principal.")
    root.destroy()