import tkinter as tk
from tkinter import messagebox
from audio_handler import start_recording, stop_recording_func

def create_main_window():
    global root, status_label, start_button, stop_button

    root = tk.Tk()
    root.title("Gravador de Áudio para Texto")
    root.geometry("300x150")

    status_label = tk.Label(root, text="Pronto para gravar", fg="blue")
    status_label.pack(pady=5)

    start_button = tk.Button(root, text="Iniciar Gravação", command=lambda: start_recording(root, status_label, start_button, stop_button), bg="green", fg="white", width=20)
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="Parar e Processar", command=lambda: stop_recording_func(root, status_label, start_button, stop_button), bg="red", fg="white", width=20, state=tk.DISABLED)
    stop_button.pack(pady=10)

    def on_closing():
        from audio_handler import on_closing
        on_closing(root)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
