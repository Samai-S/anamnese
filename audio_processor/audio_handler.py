# audio_processor/audio_handler.py
import speech_recognition as sr
from tkinter import messagebox, DISABLED, NORMAL
import tkinter as tk 
import threading
from threading import Lock, Thread
import queue 

from .multi_recognizer import MultiRecognizer 

r = sr.Recognizer()
TARGET_SAMPLE_RATE = 16000
mic = None
multi_recognizer_instance = MultiRecognizer(r) 

stop_listening_func_ref = None 
is_recording = False
processing_threads = [] 
threads_lock = Lock() 

ui_update_queue = queue.Queue()

_root_ref = None
_transcript_text_ref = None
_status_label_ref = None


def init_microphone():
    global mic
    try:
        mic = sr.Microphone(sample_rate=TARGET_SAMPLE_RATE)
        print(f"Microphone: SR={mic.SAMPLE_RATE}Hz (Target: {TARGET_SAMPLE_RATE}Hz)")
        if mic.SAMPLE_RATE != TARGET_SAMPLE_RATE:
            print("Warning: Mic SR mismatch. Quality might be affected.")
    except Exception as e:
        print(f"Error initializing mic with target SR: {e}. Using default.")
        try:
            mic = sr.Microphone()
            print(f"Microphone: Default SR={mic.SAMPLE_RATE}Hz")
        except Exception as e_default:
            print(f"Fatal: Could not initialize any microphone: {e_default}")
            mic = None
            messagebox.showerror("Erro de Microfone", "Não foi possível encontrar um microfone.")
            return False
    return True


def update_transcript_on_ui(engine_name, text):
    """Appends text to the transcript area in a thread-safe manner via queue."""
    if _transcript_text_ref and text: 
        _transcript_text_ref.config(state=NORMAL)
        _transcript_text_ref.insert(tk.END, f"[{engine_name.upper()}]: {text}\n")
        _transcript_text_ref.see(tk.END) 
        _transcript_text_ref.config(state=DISABLED)


def process_ui_updates():
    """Checks the queue for UI updates and processes them in the main thread."""
    global _root_ref
    try:
        while True: 
            engine_name, text_segment = ui_update_queue.get_nowait()
            update_transcript_on_ui(engine_name, text_segment)
            ui_update_queue.task_done()
    except queue.Empty:
        pass 
    finally:
        if _root_ref and _root_ref.winfo_exists(): # Ensure root window still exists
            _root_ref.after(100, process_ui_updates) # Check again after 100ms


def transcribe_audio_phrase_thread(audio_data):
    """
    Worker thread function to transcribe a single audio phrase.
    This is called for each phrase detected by `listen_in_background`.
    """
    global multi_recognizer_instance
    print(f"Thread {threading.current_thread().name}: Transcribing phrase (size: {len(audio_data.frame_data)} bytes)")
    try:

        results = multi_recognizer_instance.transcribe_all(audio_data)
        for engine, text in results.items():
            if text: 
                ui_update_queue.put((engine, text))
    except Exception as e:
        print(f"Error in transcription thread: {e}")
        ui_update_queue.put(("ERROR", f"Erro na transcrição da frase: {e}"))
    finally:
        with threads_lock:
            if threading.current_thread() in processing_threads:
                processing_threads.remove(threading.current_thread())
       

def audio_data_callback(recognizer, audio_phrase_data): 
    """
    Callback from listen_in_background. Called when a phrase is detected.
    """
    global is_recording
    if not is_recording:
        return

    print("\nchunk recieved")
    thread = Thread(target=transcribe_audio_phrase_thread, args=(audio_phrase_data,), daemon=True)
    with threads_lock:
        processing_threads.append(thread)
    thread.start()


def start_recording(root, status_label, start_button, stop_button, transcript_text_area):
    global stop_listening_func_ref, is_recording, mic
    global _root_ref, _transcript_text_ref, _status_label_ref

    if is_recording:
        print("Already recording!")
        return

    if mic is None: 
        if not init_microphone(): 
             messagebox.showerror("Erro de Microfone", "Microfone não está disponível.")
             return



    _root_ref = root
    _transcript_text_ref = transcript_text_area
    _status_label_ref = status_label

    _transcript_text_ref.config(state=NORMAL)
    _transcript_text_ref.delete(1.0, tk.END)
    _transcript_text_ref.insert(tk.END, "Iniciando gravação...\n")
    _transcript_text_ref.config(state=DISABLED)

    status_label.config(text="Ajustando ruído ambiente...")
    root.update_idletasks()

    try:
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
        
        r.pause_threshold = 0.8  

        stop_listening_func_ref = r.listen_in_background(mic, audio_data_callback, phrase_time_limit=4)
        
        is_recording = True
        print("Recording started...")
        status_label.config(text="Gravando... Fale agora!")
        start_button.config(state="disabled", bg="gray")
        stop_button.config(state="normal", bg="red")
        
        process_ui_updates()

    except Exception as e:
        messagebox.showerror("Erro de Gravação", f"Não foi possível iniciar a gravação:\n{e}")
        status_label.config(text="Erro ao iniciar gravação.")
        is_recording = False


def stop_recording_func(root, status_label, start_button, stop_button, transcript_text_area):
    global stop_listening_func_ref, is_recording

    if not is_recording:
        print("Not recording.")
        return

    print("Stopping recording...")
    status_label.config(text="Parando gravação...")
    root.update_idletasks()

    if stop_listening_func_ref:
        stop_listening_func_ref(wait_for_stop=True) 
        stop_listening_func_ref = None
    
    is_recording = False


    status_label.config(text="Gravação parada. Pronto.")
    start_button.config(state="normal", bg="green")
    stop_button.config(state="disabled", bg="gray")
    
    if _transcript_text_ref:
         _transcript_text_ref.config(state=NORMAL)
         _transcript_text_ref.insert(tk.END, "\n--- Gravação finalizada ---\n")
         _transcript_text_ref.config(state=DISABLED)


def on_closing(root, transcript_text_area=None): 
    global is_recording, stop_listening_func_ref, _root_ref

    print("Closing application...")
    _root_ref = None 

    if is_recording:
        print("Stopping active recording...")
        if stop_listening_func_ref:
            stop_listening_func_ref(wait_for_stop=False) 
            stop_listening_func_ref = None
        is_recording = False


    print("Waiting for any final processing...")
    threads_to_join_on_close = []
    with threads_lock:
        threads_to_join_on_close = list(processing_threads)

    for thread in threads_to_join_on_close:
        thread.join(timeout=1.0) 
    
    print("Destroying main window.")
    root.destroy()

if not init_microphone():
    print("Failed to initialize microphone at module load. Recording will likely fail.")