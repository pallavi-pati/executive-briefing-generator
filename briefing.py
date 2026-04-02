#!/usr/bin/env python3
"""
Pre-Meeting Executive Briefing Generator

Uses Claude with real-time web search to generate a comprehensive briefing
from a LinkedIn profile URL or company URL.

Usage:
    python briefing.py <url> [options]

Examples:
    python briefing.py https://linkedin.com/in/satyanadella
    python briefing.py https://linkedin.com/company/anthropic -c "Exploring partnership"
    python briefing.py https://openai.com -o briefing.md
"""

import argparse
import sys
from datetime import datetime
import anthropic


def detect_url_type(url: str) -> str:
    """Classify the URL as a LinkedIn person, LinkedIn company, or general company site."""
    url_lower = url.lower()
    if "linkedin.com/in/" in url_lower:
        return "linkedin_person"
    elif "linkedin.com/company/" in url_lower or "linkedin.com/school/" in url_lower:
        return "linkedin_company"
    else:
        return "company_website"


def build_prompt(url: str, url_type: str, meeting_context: str) -> str:
    """Build a research prompt tailored to the URL type."""
    today = datetime.now().strftime("%B %d, %Y")
    context_line = f"\n\nMeeting context: {meeting_context}" if meeting_context else ""

    if url_type == "linkedin_person":
        return f"""Today is {today}. You are an executive research assistant preparing a pre-meeting briefing.

I have an upcoming meeting with someone whose LinkedIn profile is: {url}{context_line}

Research this person thoroughly using web search, then write a professional pre-meeting executive briefing.

Do 2–3 web searches to research this person, then write the briefing. Focus on: their current role and background, their company, and any recent news.

Structure the final briefing exactly as follows (use these exact markdown headings):

# Pre-Meeting Executive Briefing

## Executive Summary
2–3 sentences: who this person is, their current role, and why this meeting is relevant.

## Professional Background
- Current role and company (with a brief company description)
- Career trajectory: key previous roles and companies
- Education
- Core areas of expertise and reputation

## About Their Company
- What the company does and its business model
- Company stage (startup/growth/public), size, and founding year
- Recent funding, acquisitions, or major milestones
- Key competitors and market position

## Recent News & Activity (Last 6 Months)
- Notable news or press mentions about this person
- Recent company news or announcements
- Any public writing, talks, or interviews they've given recently

## Key Talking Points
- Topics they are publicly passionate about or focused on
- Industry trends they are likely following
- Potential areas of mutual interest based on their background

## Suggested Questions to Ask
Provide 4–5 specific, thoughtful questions grounded in your research.

## Potential Synergies & Watch-Outs
- Opportunities for collaboration or value exchange
- Sensitive topics, controversies, or red flags to be aware of

---
*Briefing generated on {today}*"""

    else:
        # Both linkedin_company and company_website
        return f"""Today is {today}. You are an executive research assistant preparing a pre-meeting briefing.

I have an upcoming meeting with someone from this company: {url}{context_line}

Research this company thoroughly using web search, then write a professional pre-meeting executive briefing.

Do 2–3 web searches to research this company, then write the briefing. Focus on: what they do, their recent news, and their leadership.

Structure the final briefing exactly as follows (use these exact markdown headings):

# Pre-Meeting Executive Briefing

## Executive Summary
2–3 sentences: what this company does, its stage/scale, and why this meeting matters.

## Company Overview
- Core product or service and business model
- Founded, HQ, company size (headcount/revenue range if available)
- Target customers and key markets
- Funding stage or public market status

## Leadership Team
- CEO and 2–3 key executives: brief background on each
- Any notable recent leadership changes or hires

## Recent News & Developments (Last 6 Months)
- Funding rounds, acquisitions, or IPO activity
- Major product launches or partnerships
- Any layoffs, restructuring, or notable challenges
- Press coverage or analyst commentary

## Market Position & Competitive Landscape
- Top 3 competitors and how this company differentiates
- Key strengths and potential vulnerabilities
- Industry tailwinds or headwinds they're facing

## Key Talking Points
- Strategic priorities this company is publicly focused on
- Pain points or needs they likely have
- Topics that are likely top-of-mind for their leadership

## Suggested Questions to Ask
Provide 4–5 specific, research-backed questions for the meeting.

## Potential Synergies & Watch-Outs
- Opportunities: where you might add value or find common ground
- Red flags: controversies, financial stress, or sensitive topics to handle carefully

---
*Briefing generated on {today}*"""


def generate_briefing(url: str, meeting_context: str = "", output_file: str = None) -> str:
    """Run the briefing generation with streaming and live web search."""
    client = anthropic.Anthropic()

    url_type = detect_url_type(url)
    type_labels = {
        "linkedin_person": "LinkedIn Profile (Person)",
        "linkedin_company": "LinkedIn Company Page",
        "company_website": "Company Website",
    }

    print(f"\n{'═' * 62}")
    print("  PRE-MEETING EXECUTIVE BRIEFING GENERATOR")
    print(f"{'═' * 62}")
    print(f"  URL  : {url}")
    print(f"  Type : {type_labels[url_type]}")
    if meeting_context:
        print(f"  Note : {meeting_context}")
    print(f"{'═' * 62}\n")
    print("Researching via web search — this takes 30–60 seconds...\n")

    prompt = build_prompt(url, url_type, meeting_context)
    full_text_chunks: list[str] = []
    current_block_type: str | None = None
    search_count = 0

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        tools=[
            {"type": "web_search_20260209", "name": "web_search"},
            {"type": "web_fetch_20260209", "name": "web_fetch"},
        ],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for event in stream:
            etype = getattr(event, "type", None)

            if etype == "content_block_start":
                block = event.content_block
                current_block_type = block.type
                if block.type == "server_tool_use":
                    tool_name = getattr(block, "name", "tool")
                    if tool_name == "web_search":
                        search_count += 1
                        print(f"  [search #{search_count}] ", end="", flush=True)
                    elif tool_name == "web_fetch":
                        print(f"  [fetching] ", end="", flush=True)
                elif block.type == "text" and (full_text_chunks or search_count > 0):
                    print("\n" + "─" * 62 + "\n")

            elif etype == "content_block_delta":
                delta = event.delta
                dtype = getattr(delta, "type", None)

                if dtype == "input_json_delta" and current_block_type == "server_tool_use":
                    # Show partial search query as it streams in
                    partial = getattr(delta, "partial_json", "")
                    if partial:
                        print(partial, end="", flush=True)

                elif dtype == "text_delta":
                    text = delta.text
                    print(text, end="", flush=True)
                    full_text_chunks.append(text)

            elif etype == "content_block_stop":
                if current_block_type == "server_tool_use":
                    print()  # newline after search query
                current_block_type = None

        final_message = stream.get_final_message()

    briefing_text = "".join(full_text_chunks)

    # Usage summary
    usage = final_message.usage
    print(f"\n\n{'─' * 62}")
    print(
        f"  Tokens — input: {usage.input_tokens:,}  |  output: {usage.output_tokens:,}"
    )

    # Optional file save
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(briefing_text)
        print(f"  Saved  → {output_file}")

    print(f"{'─' * 62}\n")
    return briefing_text


def main():
    parser = argparse.ArgumentParser(
        prog="briefing",
        description="Generate a pre-meeting executive briefing from a LinkedIn or company URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python briefing.py https://linkedin.com/in/satyanadella
  python briefing.py https://linkedin.com/company/openai -c "Partnership discussion"
  python briefing.py https://stripe.com -o stripe_briefing.md
        """,
    )
    parser.add_argument(
        "url",
        help="LinkedIn profile, LinkedIn company page, or company website URL",
    )
    parser.add_argument(
        "-c",
        "--context",
        default="",
        metavar="TEXT",
        help="Optional meeting context (e.g. 'Evaluating them as a vendor')",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Save the briefing to a markdown file",
    )

    args = parser.parse_args()

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        print("  Set it with: export ANTHROPIC_API_KEY='sk-ant-...'", file=sys.stderr)
        sys.exit(1)

    try:
        generate_briefing(args.url, args.context, args.output)
    except anthropic.AuthenticationError:
        print("\nError: ANTHROPIC_API_KEY is invalid.", file=sys.stderr)
        print("  Get a valid key at https://console.anthropic.com", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("\nError: Could not reach the Anthropic API. Check your connection.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
