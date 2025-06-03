import tkinter as tk
from tkinter import messagebox
from audio_processor import audio_handler  
from ui import button_label 

from tkinter.scrolledtext import ScrolledText  # Adicione isso ao topo

def create_main_window():
    global root, status_label, start_button, stop_button, transcript_text_area

    root = tk.Tk()
    root.title("Gravador de Áudio para Texto")
    root.geometry("400x300")

    status_label = button_label.create_status_label(root)
    status_label.pack(pady=5)

    start_button = button_label.create_start_button(
        root,
        lambda: audio_handler.start_recording(root, status_label, start_button, stop_button, transcript_text_area)
    )
    start_button.pack(pady=10)

    stop_button = button_label.create_stop_button(
        root,
        lambda: audio_handler.stop_recording_func(root, status_label, start_button, stop_button, transcript_text_area)
    )
    stop_button.pack(pady=10)

    # Área de transcrição
    transcript_text_area = ScrolledText(root, height=8, width=45, wrap="word", state="disabled")
    transcript_text_area.pack(pady=10)

    def on_closing():
        audio_handler.on_closing(root, transcript_text_area)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

