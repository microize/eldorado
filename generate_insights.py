import os
import openai
from config import folders, OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# This is the original function, left as is.
def generate_insights(transcript_path, insights_folder):
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # Insight 1: Trading Strategies
    prompt1 = f"""Analyze the following earnings call transcript and provide actionable trading strategies. Structure the output as follows:

**Short-Term Trading:**
- [Actionable insight 1]
- [Actionable insight 2]

**Long-Term Trading:**
- [Actionable insight 1]
- [Actionable insight 2]

**Swing Trading:**
- [Actionable insight 1]
- [Actionable insight 2]

Transcript:
{transcript}
"""

    # Insight 2: Hidden Sector Insights
    prompt2 = f"""Analyze the following earnings call transcript and identify hidden insights that can be applied to the same sector. Focus on non-obvious trends, competitive advantages, or potential risks that may not be immediately apparent.

**Hidden Sector Insights:**
- [Insight 1]
- [Insight 2]

Transcript:
{transcript}
"""

    try:
        # Generate trading strategies
        response1 = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial analyst providing trading insights."},
                {"role": "user", "content": prompt1}
            ]
        )
        trading_insights = response1.choices[0].message.content

        # Generate hidden sector insights
        response2 = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial analyst providing sector-level insights."},
                {"role": "user", "content": prompt2}
            ]
        )
        sector_insights = response2.choices[0].message.content

        # Save insights to files
        base_filename = os.path.basename(transcript_path).replace(".txt", "")
        trading_insights_path = os.path.join(insights_folder, f"{base_filename}_trading_insights.md")
        sector_insights_path = os.path.join(insights_folder, f"{base_filename}_sector_insights.md")

        with open(trading_insights_path, "w", encoding="utf-8") as f:
            f.write(trading_insights)

        with open(sector_insights_path, "w", encoding="utf-8") as f:
            f.write(sector_insights)

        print(f"Successfully generated original insights for {base_filename}")

    except Exception as e:
        print(f"Failed to generate original insights for {transcript_path}: {e}")

# This is the new function, added additionally.
def generate_investment_memo(transcript_path, insights_folder):
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    prompt = f"""As a top-tier investment analyst, analyze the following earnings call transcript. Your task is to create a balanced investment memo that presents both a "Bull Case" and a "Bear Case" (Devil's Advocate view) for potential trades. This memo should encourage critical thinking and identify potential risks, aligning with the mindset of a sophisticated investor.

When formulating your analysis, consider the investment philosophies of legendary investors:
- **Warren Buffett:** Value investing, long-term perspective, economic moats, margin of safety, contrarian.
- **Peter Lynch:** Invest in what you know, growth at a reasonable price, thorough "boots-on-the-ground" research, long-term patience.
- **Ray Dalio:** Systematic and data-driven, understanding macroeconomic trends, diversification, radical transparency, continuous learning.

**Investment Memo**

**Company:** [Company Name from transcript]
**Date:** [Date of Call from transcript]

**1. Bull Case: The Opportunity**
*   **Investor Philosophy Applied:** [e.g., Warren Buffett's Value Investing]
*   [Actionable insight 1, supported by evidence from the transcript]
*   [Actionable insight 2, supported by evidence from the transcript]

**2. Bear Case: The Risks (Devil's Advocate)**
*   **Investor Philosophy Applied:** [e.g., Ray Dalio's Systematic Diversification]
*   [Counter-argument or risk 1, supported by evidence or lack thereof from the transcript]
*   [Counter-argument or risk 2, supported by evidence or lack thereof from the transcript]

**3. Summary Conclusion**
*   [A concluding paragraph on whether to invest or not, and why, synthesizing the bull and bear cases with a nod to legendary investor principles.]

Transcript:
{transcript}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a top-tier investment analyst creating a balanced investment memo."},
                {"role": "user", "content": prompt}
            ]
        )
        investment_memo = response.choices[0].message.content

        base_filename = os.path.basename(transcript_path).replace(".txt", "")
        memo_path = os.path.join(insights_folder, f"{base_filename}_investment_memo.md")

        with open(memo_path, "w", encoding="utf-8") as f:
            f.write(investment_memo)

        print(f"Successfully generated investment memo for {base_filename}")

    except Exception as e:
        print(f"Failed to generate investment memo for {transcript_path}: {e}")

def main():
    transcript_folder = folders["transcripts"]
    insights_folder = "insights"
    os.makedirs(insights_folder, exist_ok=True)

    for filename in os.listdir(transcript_folder):
        if filename.endswith(".txt"):
            transcript_path = os.path.join(transcript_folder, filename)
            # Call the original function
            generate_insights(transcript_path, insights_folder)
            # Call the new function
            generate_investment_memo(transcript_path, insights_folder)

if __name__ == "__main__":
    main()
