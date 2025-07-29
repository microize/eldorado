from itables import init_notebook_mode, show
from data_processing import (
    fetch_announcements,
    download_pdfs,
    extract_text_from_pdfs,
    find_audio_links,
    process_audio,
    transcribe_all_audio,
)
from config import OPENAI_API_KEY

print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")

# Interactive DataFrames
init_notebook_mode(all_interactive=True)

# --- Full Pipeline ---
def run_pipeline(user_keywords=["Q1"]):
    announcements = fetch_announcements()
    pdf_status = download_pdfs(announcements)
    text_status = extract_text_from_pdfs()
    audio_links = find_audio_links(user_keywords=user_keywords)
    audio_files = process_audio(audio_links)
    final_output = transcribe_all_audio(audio_files)
    
    # Generate insights
    import generate_insights
    generate_insights.main()
    
    final_output.to_csv("all_investor_calls_with_detailed_logs.csv", index=False)
    print("\nPipeline complete. Results saved to all_investor_calls_with_detailed_logs.csv")
    show(final_output)
    return final_output

# --- To Run ---
if __name__ == "__main__":
    final_results = run_pipeline(user_keywords=["Q1"])
