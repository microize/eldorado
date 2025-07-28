# Project Eldorado

This project is a Python application that fetches investor call information, processes audio, and generates transcripts, along with generating investment insights.

## Project Structure

The project is organized into several modules for better maintainability and readability:

*   `app.py`: The main entry point for running the entire pipeline.
*   `config.py`: Contains configuration variables, including API keys and folder paths.
*   `utils.py`: Provides utility functions such as logging, web fetching (curl and Playwright), and URL cleaning.
*   `llm.py`: Handles all interactions with Large Language Models (LLMs) for media link extraction and information parsing.
*   `audio_processing.py`: Contains functions for downloading, speeding up, splitting, and transcribing audio files.
*   `data_processing.py`: Manages the core data processing pipeline, including fetching announcements, downloading PDFs, extracting text, finding audio links, and processing audio.
*   `generate_insights.py`: A new script responsible for generating various investment insights from the transcribed earnings calls, including trading strategies, hidden sector insights, and a detailed investment memo with bull and bear cases.

## Setup

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

3.  **Install system dependencies:**
    The `pyaudio` and `pydub` packages requires the `portaudio` and `ffmpeg` libraries to be installed on your system.

    - On Debian/Ubuntu-based systems, run:
      ```bash
      sudo apt-get install -y portaudio19-dev ffmpeg
      ```

4.  **Install Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Install Playwright browsers and dependencies (after activating virtual environment):**
   ```bash
   playwright install-deps
   playwright install
   ```

6. **Set OpenAI API Key:**
   You need to set your OpenAI API key as an environment variable. You can do this by running the following command in your terminal, replacing `your_api_key` with your actual key:
   ```bash
   export OPENAI_API_KEY='your_api_key'
   ```
   To make this permanent, you can add this line to your shell's startup file (e.g., `~/.bashrc`, `~/.zshrc`).

## Running the script

Once you have completed the setup, you can run the application with:

```bash
python app.py
```

This will execute the full pipeline, including fetching announcements, processing audio, transcribing, and generating investment insights into the `insights/` directory.