from tkinter import messagebox
from deepseek_api import produces_anamnese

def output_text(text):
    try:
        with produces_anamnese(text) as f:
            print("\n")
    except Exception as e:
        messagebox.showerror("Erro ao chamar a funcao produces_anamnese", f"Call error:\n{e}")
