import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"


def log_file_path(filename):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR / filename

def setup_logging():
    logging.basicConfig(
        filename=log_file_path('debug_log.txt'),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'
    )
    
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

class YtDlpLogger:
    def __init__(self):
        self.warning_callback = None

    def debug(self, msg):
        if not msg.startswith('[debug] '):
            logging.debug(f"[YT-DLP] {msg}")

    def info(self, msg):
        logging.info(f"[YT-DLP] {msg}")

    def warning(self, msg):
        logging.warning(f"[YT-DLP] {msg}")
        if self.warning_callback:
            self.warning_callback(msg)

    def error(self, msg):
        logging.error(f"[YT-DLP] {msg}")
