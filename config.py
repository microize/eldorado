
import os

# Manually read and set the environment variable
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Base directory for the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data folders
DATA_DIR = os.path.join(BASE_DIR, '01.text')
NSE_PDFS_DIR = os.path.join(DATA_DIR, 'nse_pdfs')
PROCESS_LOGS_DIR = os.path.join(DATA_DIR, 'process_logs')
RAW_TEXTS_DIR = os.path.join(DATA_DIR, 'raw_texts')
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, 'transcripts')

# Audio folders
AUDIO_DIR = os.path.join(BASE_DIR, '02.audio')
AUDIO_FILES_DIR = os.path.join(AUDIO_DIR, 'audio_files')
SPED_AUDIO_FILES_DIR = os.path.join(AUDIO_DIR, 'sped_audio_files')

# Insights folder
INSIGHTS_DIR = os.path.join(BASE_DIR, 'insights')

# A dictionary to easily access all folder paths
folders = {
    "nse_pdfs": NSE_PDFS_DIR,
    "process_logs": PROCESS_LOGS_DIR,
    "raw_texts": RAW_TEXTS_DIR,
    "transcripts": TRANSCRIPTS_DIR,
    "audio_files": AUDIO_FILES_DIR,
    "sped_audio_files": SPED_AUDIO_FILES_DIR,
    "insights": INSIGHTS_DIR,
}

# Create directories if they don't exist
for folder_path in folders.values():
    os.makedirs(folder_path, exist_ok=True)
