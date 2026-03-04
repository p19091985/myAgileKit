import tkinter as tk
from tkinter import ttk
import traceback
from .logger import setup_logging
from .ui import YoutubeDownloaderApp

def main():
    setup_logging()
    
    try:
        root = tk.Tk()
        try:
            style = ttk.Style()
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
        except:
            pass
            
        app = YoutubeDownloaderApp(root)
        root.mainloop()
        
    except Exception as e:
        with open("debug_log.txt", "a") as f:
            f.write(f"\nCRASH DE INICIALIZAÇÃO:\n{traceback.format_exc()}")
        print(f"Erro crítico: {e}")

if __name__ == "__main__":
    main()
