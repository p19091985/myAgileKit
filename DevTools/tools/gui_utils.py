import tkinter as tk
from tkinter import ttk
import sys
import os
import logging
import shutil
import datetime

# --- CONTRANTS ---
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
MIN_WIDTH = 800
MIN_HEIGHT = 600

COLOR_BG = "#f0f0f0"
COLOR_PRIMARY = "#007bff" # Example blue
COLOR_TEXT = "#333333"

if sys.platform == "win32":
    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Consolas"
elif sys.platform == "darwin":
    FONT_FAMILY = "San Francisco" # Often needs check, but system font alias works
    FONT_MONO = "Menlo"
else:
    FONT_FAMILY = "Liberation Sans" # Common on Linux
    FONT_MONO = "DejaVu Sans Mono"

# Fallback mechanism could be more complex, but this is a good start
try:
    # Check if fonts exist (optional, but good for robustness)
    # tkinter.font.families() requires root, which might not exist yet.
    # We will stick to safe defaults or let Tkinter handle fallback.
    pass 
except:
    pass

FONT_H1 = (FONT_FAMILY, 18, 'bold')
FONT_H2 = (FONT_FAMILY, 12, 'bold')
FONT_BODY = (FONT_FAMILY, 10)
FONT_CODE = (FONT_MONO, 9)

# --- SETUP FUNCTIONS ---

def setup_window(root, title="DevTools"):
    """Configures the main window with standard settings."""
    root.title(title)
    
    # Center window
    root.update_idletasks() # Ensure accurate geometry calculations
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = int((screen_width - WINDOW_WIDTH) / 2)
    y = int((screen_height - WINDOW_HEIGHT) / 2)
    
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
    root.minsize(MIN_WIDTH, MIN_HEIGHT)
    
    # Configure Theme
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass # Fallback to default if clam not available

    # Standard Styles
    style.configure('.', font=FONT_BODY, background=COLOR_BG, foreground=COLOR_TEXT)
    style.configure('TFrame', background=COLOR_BG)
    style.configure('TLabel', background=COLOR_BG, foreground=COLOR_TEXT)
    style.configure('TButton', font=FONT_BODY)
    style.configure('Header.TFrame', background='#e0e0e0')
    style.configure('Title.TLabel', font=FONT_H1, background=COLOR_BG)
    style.configure('Subtitle.TLabel', font=FONT_H2, foreground='#666')
    style.configure('Primary.TButton', font=(FONT_FAMILY, 10, 'bold'))
    
    root.configure(bg=COLOR_BG)

def create_header(parent, title, subtitle=None):
    """Creates a standard header frame."""
    header_frame = ttk.Frame(parent, padding=(20, 20, 20, 10))
    header_frame.pack(fill='x')
    
    title_lbl = ttk.Label(header_frame, text=title, style='Title.TLabel')
    title_lbl.pack(anchor='w')
    
    if subtitle:
        sub_lbl = ttk.Label(header_frame, text=subtitle, style='Subtitle.TLabel')
        sub_lbl.pack(anchor='w', pady=(5, 0))
        
    ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=20, pady=(0, 10))
    return header_frame

def create_footer(parent, text="DevTools v1.0"):
    """Creates a standard footer."""
    footer_frame = ttk.Frame(parent, padding=10)
    footer_frame.pack(side='bottom', fill='x')
    
    ttk.Separator(footer_frame, orient='horizontal').pack(fill='x', pady=(0, 5))
    lbl = ttk.Label(footer_frame, text=text, foreground='gray', font=(FONT_FAMILY, 8))
    lbl.pack(anchor='e')
    return footer_frame

def get_script_directory():
    """Returns the directory of the running script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # If running from a tool script inside tools/, we might want to know where main.py is, 
        # but usually we just want the script's own dir.
        return os.path.dirname(os.path.abspath(sys.argv[0]))

# --- LOGGING & BACKUP ---

class GuiHandler(logging.Handler):
    """Logging handler that writes to a Tkinter Text widget."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.config(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.config(state='disabled')
        # Schedule update in the main GUI thread
        self.text_widget.after(0, append)

def setup_logger(name, log_file, text_widget=None):
    """
    Sets up a logger that writes to a file and optionally a GUI Text widget.
    
    Args:
        name: Header/Name of the logger.
        log_file: Path to the log file.
        text_widget: Optional Tkinter Text widget to display logs.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers = [] # Clear existing handlers to avoid duplicates

    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler (for debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # GUI Handler
    if text_widget:
        gui_handler = GuiHandler(text_widget)
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)

    return logger

def create_backup(file_path, logger=None):
    """Creates a .bak copy of the file."""
    try:
        backup_path = file_path + ".bak"
        shutil.copy2(file_path, backup_path)
        if logger:
            logger.info(f"Backup criado: {os.path.basename(backup_path)}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"Falha ao criar backup de {file_path}: {e}")
        return False
