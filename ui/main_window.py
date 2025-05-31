import tkinter as tk
from tkinter import messagebox
from audio_processor import audio_handler  # Certifique-se de que esse caminho está correto
from ui import button_label  # Certifique-se de que button_label.py está dentro da pasta ui/

def create_main_window():
    # Tornando variáveis globais caso precise acessar de fora (opcional)
    global root, status_label, start_button, stop_button

    # Criação da janela principal
    root = tk.Tk()
    root.title("Gravador de Áudio para Texto")
    root.geometry("300x150")

    # Label de status
    status_label = button_label.create_status_label(root)
    status_label.pack(pady=5)

    # Botão Iniciar Gravação
    start_button = button_label.create_start_button(
        root,
        lambda: audio_handler.start_recording(root, status_label, start_button, stop_button)
    )
    start_button.pack(pady=10)

    # Botão Parar Gravação
    stop_button = button_label.create_stop_button(
        root,
        lambda: audio_handler.stop_recording_func(root, status_label, start_button, stop_button)
    )
    stop_button.pack(pady=10)

    # Tratamento do fechamento da janela
    def on_closing():
        audio_handler.on_closing(root)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
