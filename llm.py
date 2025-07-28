import re
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import openai
from bs4 import BeautifulSoup
from config import OPENAI_API_KEY
from utils import fetch_dynamic_html, fetch_with_curl, clean_url, log_step

openai.api_key = OPENAI_API_KEY

class InvestorCallInfo(BaseModel):
    url: str = Field(description="URL of the investor/analyst call recording, or 'No link found'.")
    audio_flag: bool = Field(description="True if direct audio/video file link or can be scraped, otherwise False.")

parser = PydanticOutputParser(pydantic_object=InvestorCallInfo)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
prompt = PromptTemplate(
    template="""
Extract the following information from the text below:
1. The URL (if any) where the investor/analyst conference call recording (audio or video) is hosted.
2. Whether it explicitly mentions it is an audio recording.

Return strictly as JSON:
{format_instructions}

Text:
{text}
""",
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

def gpt_extract_media_link(url, keywords=["Q1"]):
    html_content = fetch_dynamic_html(url) or fetch_with_curl(url)
    soup = BeautifulSoup(html_content, 'html.parser')

    # First, try to find iframes with YouTube links
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if src and ("youtube.com/embed" in src or "youtube.com/watch" in src):
            print(f"""
Found YouTube iframe: {src}
""")
            return clean_url(src)

    keyword_list = ", ".join(keywords)

    if not html_content:
        print(f"""
Failed to fetch HTML content for {url}. Skipping GPT extraction.
""")
        return ""

    # Check <a> tags for direct media links or YouTube links
    media_exts = (".mp3", ".wav", ".aac", ".m4a", ".ogg", ".mp4", ".webm", ".mov", ".avi", ".flv", ".wmv")
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')
        if href:
            if href.lower().endswith(media_exts):
                print(f"""
Found direct media link in <a> tag: {href}
""")
                return clean_url(href)
            if "youtube.com/watch" in href or "youtu.be/" in href:
                print(f"""
Found YouTube link in <a> tag: {href}
""")
                return clean_url(href)

    # Regex to find direct audio/video links (fallback if not found in <a> tags)
    media_regex = r'(https?://[\w./-]+?\.(?:mp3|mp4|m4a|aac|ogg|wav|webm|mov|avi|flv|wmv))'
    direct_media_links = re.findall(media_regex, html_content, re.IGNORECASE)
    if direct_media_links:
        print(f"""
Found direct media link via regex: {direct_media_links[0]}
""")
        return clean_url(direct_media_links[0])

    # Extract all hrefs from <a> tags (for LLM context if direct links not found)
    all_links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
    links_text = "\n".join(all_links)

    print(f"""
HTML content sent to GPT for {url}:
{html_content[:15000]}
""") # Debugging print
    print(f"""
Extracted links sent to GPT for {url}:
{links_text}
""") # Debugging print

    gpt_prompt = """
    The following is HTML from a webpage related to an investor call.
    Your task is to find the direct URL for the audio or video recording (e.g., .mp3, .mp4, .m4a) or a link to a video platform (e.g., YouTube, Vimeo).

    Prioritize direct media file links. If not found, look for links to video platforms.

    Look for the most relevant link that matches any of these keywords: "{keyword_list}".

    Consider the following extracted links from <a> tags:
    {links_text}

    Search for:
    1.  Direct links to media files (e.g., <a href=".../recording.mp3">, <source src=".../audio.mp4">, <video src=".../video.m4a">).
    2.  Links to known video platforms like YouTube, Vimeo, or other webcast services (e.g., <a href="https://www.youtube.com/watch?v=...">, <a href="https://vimeo.com/...">).
    3.  Links within <a> tags that contain keywords like "audio", "video", "recording", "webcast", "playback", "listen", "watch", "replay", "investor call", "earnings call", "conference call", "analyst meet", "presentation", "event", "media", "archive", "download".
    4.  Also, look for direct URLs within the raw HTML content, even if not explicitly in <a> tags (e.g., in <script> tags, or as part of text).

    If you find a relevant URL, return only the URL. Ensure the URL is complete and valid.
    If no such link exists, reply exactly with "No link found".

    HTML:
    {html_content}
    """.format(
        keyword_list=keyword_list,
        links_text=links_text,
        html_content=html_content[:15000]
    )
    try:
        ai_resp = llm.invoke(gpt_prompt).content.strip()
        print(f"""
GPT Scrape Output for {url}:
{ai_resp}
""")
        return clean_url(ai_resp) if "http" in ai_resp and "No link found" not in ai_resp else ""
    except Exception as e:
        print(f"GPT extraction failed for {url}: {e}")
        return ""

def extract_info_with_langchain(text, pdf_file):
    try:
        log_step(pdf_file, "LangChainExtraction", "Started")
        _prompt = prompt.format_prompt(text=text)
        output = llm.invoke(_prompt.to_string())
        parsed = parser.parse(output.content)
        url_lower = parsed.url.lower()
        media_exts = (".mp3", ".wav", ".aac", ".m4a", ".ogg", ".mp4")
        parsed.audio_flag = any(url_lower.endswith(ext) for ext in media_exts) or \
                            "youtube.com" in url_lower or "soundcloud.com" in url_lower
        log_step(pdf_file, "LangChainExtraction", "Completed", {"url": parsed.url, "audio_flag": parsed.audio_flag})
        return parsed
    except Exception as e:
        log_step(pdf_file, "LangChainExtraction", "Failed", {"error": str(e)})
        return InvestorCallInfo(url="Error", audio_flag=False)