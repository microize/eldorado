import os
import requests
import pandas as pd
from PyPDF2 import PdfReader
from itables import show
from config import folders
from utils import log_step, clean_url
from llm import extract_info_with_langchain, gpt_extract_media_link
from audio_processing import download_audio, speed_up_audio, transcribe_long_audio

def fetch_announcements():
    categories = {"Equity": "equities", "SME": "sme"}
    base_url = "https://www.nseindia.com/api/corporate-announcements?index={}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    all_data = []
    with requests.Session() as session:
        session.headers.update(headers)
        session.get("https://www.nseindia.com/companies-listing/corporate-filings-announcements")
        for name, param in categories.items():
            url = base_url.format(param)
            resp = session.get(url)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    for row in data:
                        row["Category"] = name
                        all_data.append(row)
                except Exception:
                    print(f"Failed to parse JSON for {url}")
    df = pd.DataFrame(all_data)
    return df[df["desc"].str.contains("Analysts/Institutional Investor Meet/Con. Call Updates", case=False, na=False)]

def download_pdfs(df, output_folder=folders["pdf"]):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    downloaded_files = []
    links = df["attchmntFile"].dropna().unique().tolist() if "attchmntFile" in df.columns else []
    for link in links:
        try:
            filename = link.split("/")[-1]
            pdf_path = os.path.join(output_folder, filename)
            r = requests.get(link, headers=headers, timeout=15)
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r.content)
            downloaded_files.append({"PDF File": filename, "Status": "Downloaded"})
        except Exception as e:
            downloaded_files.append({"PDF File": link.split("/")[-1], "Status": f"Failed: {e}"})
    return pd.DataFrame(downloaded_files)

def extract_text_from_pdfs(pdf_folder=folders["pdf"], raw_text_folder=folders["raw_texts"]):
    extracted_files = []
    for pdf_file in os.listdir(pdf_folder):
        if not pdf_file.endswith(".pdf"): continue
        try:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            reader = PdfReader(pdf_path)
            text_content = "".join(page.extract_text() or "" for page in reader.pages)
            raw_text_file = os.path.join(raw_text_folder, pdf_file.replace(".pdf", ".txt"))
            with open(raw_text_file, "w", encoding="utf-8") as f:
                f.write(text_content)
            log_step(pdf_file, "PDFProcessing", "TextExtracted", {"raw_text": raw_text_file})
            extracted_files.append({"PDF File": pdf_file, "Raw Text": raw_text_file})
        except Exception as e:
            extracted_files.append({"PDF File": pdf_file, "Raw Text": f"Failed: {e}"})
    return pd.DataFrame(extracted_files)

def find_audio_links(raw_text_folder=folders["raw_texts"], user_keywords=["Q1"]):
    results = []
    for txt_file in os.listdir(raw_text_folder):
        if not txt_file.endswith(".txt"):
            continue
        pdf_name = txt_file.replace(".txt", ".pdf")
        with open(os.path.join(raw_text_folder, txt_file), "r", encoding="utf-8") as f:
            text_content = f.read()

        parsed = extract_info_with_langchain(text_content, pdf_name)
        final_audio_url = clean_url(parsed.url)
        investor_file_link_flag = bool(final_audio_url and "http" in final_audio_url)

        if investor_file_link_flag and not parsed.audio_flag:
            media_url = gpt_extract_media_link(final_audio_url, user_keywords)
            if media_url:
                final_audio_url = media_url
                parsed.audio_flag = True
                log_step(pdf_name, "GPTDynamicScrape", "FoundMediaLink", {"final_url": final_audio_url})
            else:
                final_audio_url = "" # Explicitly set to empty if no media_url found
                log_step(pdf_name, "GPTDynamicScrape", "NoLinkFound", {"keywords": user_keywords})

        results.append({
            "PDF File": pdf_name,
            "Audio URL": final_audio_url,
            "audio_flag": parsed.audio_flag,
            "investor_file_link_flag": investor_file_link_flag
        })

    df = pd.DataFrame(results)
    show(df)
    return df

def process_audio(audio_df, audio_folder=folders["audio"], sped_folder=folders["sped_audio"]):
    results = []
    media_exts = (".mp3", ".wav", ".aac", ".m4a", ".ogg", ".mp4", ".webm", ".mov", ".avi", ".flv", ".wmv")
    for _, row in audio_df.iterrows():
        pdf_file, url = row["PDF File"], row["Audio URL"]
        print(f"\nProcessing audio for PDF: {pdf_file}, URL: {url}")
        if not url or (not url.lower().endswith(media_exts) and "youtube.com" not in url.lower() and "youtu.be" not in url.lower()):
            print(f"Skipping {url} - not a recognized media or YouTube link.")
            results.append({**row, "Original Audio": "No audio", "Sped Audio": "No audio"})
            continue
        audio_ext = os.path.splitext(url)[-1]
        original_audio = os.path.join(audio_folder, pdf_file.replace(".pdf", audio_ext))
        downloaded = download_audio(url, original_audio, pdf_file)
        if downloaded:
            sped_audio = os.path.join(sped_folder, os.path.basename(original_audio))
            sped_audio = speed_up_audio(downloaded, sped_audio, pdf_file)
            results.append({**row, "Original Audio": original_audio, "Sped Audio": sped_audio})
        else:
            results.append({**row, "Original Audio": "Failed", "Sped Audio": "Failed"})
    return pd.DataFrame(results)

def transcribe_all_audio(audio_df, transcript_folder=folders["transcripts"]):
    results = []
    for _, row in audio_df.iterrows():
        pdf_file, sped_audio = row["PDF File"], row.get("Sped Audio", "")
        if not sped_audio or "No audio" in sped_audio or "Failed" in sped_audio:
            results.append({**row, "Transcript": "No transcript"})
            continue
        transcript_text = transcribe_long_audio(sped_audio, pdf_file)
        transcript_file = os.path.join(transcript_folder, pdf_file.replace(".pdf", ".txt"))
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        log_step(pdf_file, "Transcription", "FinalTranscriptSaved", {"file": transcript_file})
        results.append({**row, "Transcript": transcript_file})
    return pd.DataFrame(results)
