import os
import subprocess
import requests
from pydub import AudioSegment
import openai
from utils import log_step

def download_audio(url, output_path, pdf_file):
    try:
        log_step(pdf_file, "AudioDownload", "Started", {"url": url})
        if "youtube.com" in url or "youtu.be" in url or "vimeo.com" in url:
            command = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_path, url]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        else:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(r.content)
        log_step(pdf_file, "AudioDownload", "Completed", {"saved_to": output_path})
        return output_path
    except Exception as e:
        error_details = str(e)
        if isinstance(e, subprocess.CalledProcessError):
            error_details += f"\nStderr: {e.stderr.strip()}"
        print(f"Error downloading {url}: {error_details}") # Added detailed print
        log_step(pdf_file, "AudioDownload", "Failed", {"error": error_details})
        return None

def speed_up_audio(input_path, output_path, pdf_file, speed=1.25):
    try:
        log_step(pdf_file, "AudioSpeedUp", "Started")
        sound = AudioSegment.from_file(input_path)
        sped = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}).set_frame_rate(sound.frame_rate)
        sped.export(output_path, format=os.path.splitext(output_path)[-1][1:])
        log_step(pdf_file, "AudioSpeedUp", "Completed", {"sped_audio": output_path})
        return output_path
    except Exception as e:
        print(f"Error speeding up audio {input_path}: {e}") # Added detailed print
        log_step(pdf_file, "AudioSpeedUp", "Failed", {"error": str(e)})
        return None

def split_audio(input_path, pdf_file, max_seconds=1380):
    try:
        log_step(pdf_file, "AudioSplit", "Started")
        sound = AudioSegment.from_file(input_path)
        chunks = []
        for i in range(0, len(sound), max_seconds * 1000):
            chunk_path = input_path.replace(".mp3", f"_part{i//(max_seconds*1000)+1}.mp3")
            sound[i:i+max_seconds*1000].export(chunk_path, format="mp3")
            chunks.append(chunk_path)
        log_step(pdf_file, "AudioSplit", "Completed", {"chunks": chunks})
        return chunks
    except Exception as e:
        log_step(pdf_file, "AudioSplit", "Failed", {"error": str(e)})
        return []

def transcribe_long_audio(audio_path, pdf_file):
    transcripts = []
    chunks = split_audio(audio_path, pdf_file)
    for idx, chunk in enumerate(chunks, start=1):
        try:
            log_step(pdf_file, "Transcription", "Started", {"chunk": chunk})
            with open(chunk, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="gpt-4o-transcribe", file=audio_file
                )
            transcripts.append(transcript.text)
            log_step(pdf_file, "Transcription", "Completed", {"chunk": chunk})
        except Exception as e:
            transcripts.append(f"Failed to transcribe {chunk}: {e}")
            log_step(pdf_file, "Transcription", "Failed", {"chunk": chunk, "error": str(e)})
    return "\n".join(transcripts)
