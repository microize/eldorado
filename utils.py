import os
import json
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright
from config import folders

def log_step(pdf_file, step, status, extra=None):
    log_file = os.path.join(folders["process_logs"], pdf_file.replace(".pdf", "_log.json"))
    log_data = {"timestamp": datetime.now().isoformat(), "step": step, "status": status, "extra": extra or {}}
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(log_data)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

def fetch_with_curl(url):
    try:
        result = subprocess.run(["curl", "-k", "-s", url], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        print(f"Curl fetch failed for {url}: {e}")
        return ""

def fetch_dynamic_html(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=120000, wait_until='domcontentloaded')
            page.wait_for_selector('body', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            html_content = page.content()
            browser.close()
            return html_content
    except Exception as e:
        print(f"Dynamic fetch failed for {url}: {e}")
        return ""

def clean_url(url):
    return url.replace(" ", "").replace("%20", "") if url else url
