import tkinter as tk

def create_status_label(parent):
    return tk.Label(parent, text="Pronto para gravar", fg="blue")

def create_start_button(parent, command):
    return tk.Button(
        parent,
        text="Iniciar Gravação",
        command=command,
        bg="green",
        fg="white",
        width=20
    )

def create_stop_button(parent, command):
    return tk.Button(
        parent,
        text="Parar e Processar",
        command=command,
        bg="red",
        fg="white",
        width=20,
        state=tk.DISABLED
    )
