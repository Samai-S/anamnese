# audio_processor/audio_handler.py

import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox, DISABLED, NORMAL
from threading import Lock, Thread
import queue

from .multi_recognizer import MultiRecognizer
from .dynamic_audio_recorder import DynamicAudioRecorder

# Constantes
TARGET_SAMPLE_RATE = 16000

# Instâncias globais
r = sr.Recognizer()
mic = None
multi_recognizer_instance = MultiRecognizer(r)
dynamic_recorder = None

# Controle de gravação e threads
is_recording = False
processing_threads = []
threads_lock = Lock()

# Fila para atualizar interface
ui_update_queue = queue.Queue()

# Referências para widgets do Tkinter
_root_ref = None
_transcript_text_ref = None
_status_label_ref = None


def init_microphone():
    global mic
    try:
        mic = sr.Microphone(sample_rate=TARGET_SAMPLE_RATE)
        print(f"Microfone: {mic.SAMPLE_RATE} Hz (alvo: {TARGET_SAMPLE_RATE} Hz)")
        if mic.SAMPLE_RATE != TARGET_SAMPLE_RATE:
            print("⚠️ Aviso: taxa de amostragem diferente da esperada.")
    except Exception as e:
        print(f"Erro com SR={TARGET_SAMPLE_RATE}: {e}. Tentando padrão.")
        try:
            mic = sr.Microphone()
            print(f"Microfone padrão: {mic.SAMPLE_RATE} Hz")
        except Exception as e_default:
            print(f"❌ Não foi possível inicializar o microfone: {e_default}")
            mic = None
            messagebox.showerror("Erro de Microfone", "Não foi possível encontrar um microfone.")
            return False
    return True


def update_transcript_on_ui(engine_name, text):
    """Atualiza o campo de transcrição na interface (thread-safe via fila)."""
    if _transcript_text_ref and text:
        _transcript_text_ref.config(state=NORMAL)
        _transcript_text_ref.insert(tk.END, f"[{engine_name.upper()}]: {text}\n")
        _transcript_text_ref.see(tk.END)
        _transcript_text_ref.config(state=DISABLED)


def process_ui_updates():
    """Verifica a fila e processa atualizações de interface."""
    global _root_ref
    try:
        while True:
            engine_name, text_segment = ui_update_queue.get_nowait()
            update_transcript_on_ui(engine_name, text_segment)
            ui_update_queue.task_done()
    except queue.Empty:
        pass
    finally:
        if _root_ref and _root_ref.winfo_exists():
            _root_ref.after(100, process_ui_updates)


def transcribe_audio_phrase_thread(audio_data):
    """Thread que chama os reconhecedores para um trecho de áudio."""
    global multi_recognizer_instance
    print(f"🎧 Transcrevendo (tamanho: {len(audio_data.frame_data)} bytes)")
    try:
        results = multi_recognizer_instance.transcribe_all(audio_data)
        for engine, text in results.items():
            if text:
                ui_update_queue.put((engine, text))
    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")
        ui_update_queue.put(("ERRO", f"Erro na transcrição: {e}"))
    finally:
        with threads_lock:
            t = Thread.current_thread()
            if t in processing_threads:
                processing_threads.remove(t)


def start_recording(root, status_label, start_button, stop_button, transcript_text_area):
    global is_recording, mic, _root_ref, _transcript_text_ref, _status_label_ref, dynamic_recorder

    if is_recording:
        print("⚠️ Já está gravando.")
        return

    if mic is None:
        if not init_microphone():
            messagebox.showerror("Erro de Microfone", "Microfone não disponível.")
            return

    _root_ref = root
    _transcript_text_ref = transcript_text_area
    _status_label_ref = status_label

    _transcript_text_ref.config(state=NORMAL)
    _transcript_text_ref.delete(1.0, tk.END)
    _transcript_text_ref.insert(tk.END, "🎙️ Iniciando gravação...\n")
    _transcript_text_ref.config(state=DISABLED)

    status_label.config(text="Ajustando ruído ambiente...")
    root.update_idletasks()

    try:
        dynamic_recorder = DynamicAudioRecorder(
            recognizer=r,
            mic=mic,
            transcribe_callback=transcribe_audio_phrase_thread,
            pause_threshold=2.0
        )

        is_recording = True
        dynamic_recorder.start()

        status_label.config(text="Gravando... fale algo.")
        start_button.config(state="disabled", bg="gray")
        stop_button.config(state="normal", bg="red")

        process_ui_updates()

    except Exception as e:
        messagebox.showerror("Erro ao iniciar", f"Erro ao iniciar gravação: {e}")
        status_label.config(text="Erro ao iniciar.")
        is_recording = False


def stop_recording_func(root, status_label, start_button, stop_button, transcript_text_area):
    global is_recording, dynamic_recorder

    if not is_recording:
        print("⚠️ Gravação já estava parada.")
        return

    print("⏹️ Parando gravação...")
    status_label.config(text="Parando gravação...")
    root.update_idletasks()

    if dynamic_recorder:
        dynamic_recorder.stop()
        dynamic_recorder = None

    is_recording = False

    status_label.config(text="Gravação parada.")
    start_button.config(state="normal", bg="green")
    stop_button.config(state="disabled", bg="gray")

    if _transcript_text_ref:
        _transcript_text_ref.config(state=NORMAL)
        _transcript_text_ref.insert(tk.END, "\n--- Gravação finalizada ---\n")
        _transcript_text_ref.config(state=DISABLED)


def on_closing(root, transcript_text_area=None):
    global is_recording, dynamic_recorder, _root_ref

    print("🧹 Encerrando aplicação...")
    _root_ref = None

    if is_recording:
        print("⏸️ Parando gravação ativa...")
        if dynamic_recorder:
            dynamic_recorder.stop()
            dynamic_recorder = None
        is_recording = False

    print("⏳ Aguardando finalização de transcrições...")
    threads_to_join = []
    with threads_lock:
        threads_to_join = list(processing_threads)

    for t in threads_to_join:
        t.join(timeout=1.0)

    print("✅ Encerrando janela principal.")
    root.destroy()


# Inicialização automática do microfone (opcional)
if not init_microphone():
    print("❌ Falha ao inicializar microfone no carregamento.")
