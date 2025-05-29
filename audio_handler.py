import speech_recognition as sr
from tkinter import messagebox
from threading import Thread
from file_handler import output_text

r = sr.Recognizer()
mic = sr.Microphone()
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
            r.adjust_for_ambient_noise(source, duration=0.7)
        stop_listening = r.listen_in_background(mic, audio_callback)
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
        stop_listening(wait_for_stop=False)
        stop_listening = None

    is_recording = False
    start_button.config(state="normal", bg="green")
    stop_button.config(state="disabled", bg="gray")

    if audio_chunks:
        status_label.config(text="Processando áudio...")
        processing_thread = Thread(target=lambda: process_audio_data(status_label))
        processing_thread.start()
    else:
        print("Nenhum áudio gravado.")
        status_label.config(text="Nenhum áudio gravado.")

def process_audio_data(status_label):
    global audio_chunks
    print("Iniciando reconhecimento...")

    try:
        sample_rate = mic.SAMPLE_RATE
        sample_width = mic.SAMPLE_WIDTH
    except AttributeError:
        print("Warning: usando sample rate padrão.")
        sample_rate = 44100
        sample_width = 2

    if not audio_chunks:
        print("Sem áudio.")
        status_label.config(text="Erro: Sem dados de áudio.")
        return

    combined_data = b"".join(audio_chunks)
    combined_audio = sr.AudioData(combined_data, sample_rate, sample_width)

    try:
        text = r.recognize_google(combined_audio, language="pt-BR")
        print("Texto reconhecido:", text)
        ##output_text(text)
        status_label.config(text="Texto salvo em output.txt")
    except sr.UnknownValueError:
        status_label.config(text="Não foi possível entender o áudio.")
    except sr.RequestError as e:
        messagebox.showerror("Erro de Rede", f"Erro ao conectar ao serviço:\n{e}")
        status_label.config(text="Erro de rede.")
    except Exception as e:
        status_label.config(text=f"Erro: {e}")
    finally:
        audio_chunks.clear()

def on_closing(root):
    global stop_listening, is_recording, processing_thread
    if is_recording and stop_listening:
        stop_listening(wait_for_stop=False)
    if processing_thread and processing_thread.is_alive():
        print("Aguardando processamento terminar...")
    root.destroy()
