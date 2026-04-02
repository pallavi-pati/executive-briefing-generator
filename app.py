import streamlit as st
import anthropic
from tavily import TavilyClient
from briefing import detect_url_type

st.set_page_config(
    page_title="Executive Briefing Generator",
    page_icon="📋",
    layout="centered",
)

st.title("📋 Executive Briefing Generator")
st.caption("Paste a LinkedIn profile, LinkedIn company page, or any company website URL to generate a pre-meeting briefing.")

url = st.text_input(
    "URL",
    placeholder="https://linkedin.com/in/satyanadella  or  https://stripe.com",
)
context = st.text_input(
    "Meeting context (optional)",
    placeholder="e.g. Exploring a partnership, evaluating as a vendor...",
)

if st.button("Generate Briefing", type="primary", disabled=not url):
    try:
        anthropic_key = st.secrets["ANTHROPIC_API_KEY"]
        tavily_key = st.secrets["TAVILY_API_KEY"]
    except KeyError as e:
        st.error(f"{e} not found in Streamlit secrets.")
        st.stop()

    url_type = detect_url_type(url)

    try:
        # --- Step 1: build search queries based on URL type ---
        tavily = TavilyClient(api_key=tavily_key)

        with st.status("Searching the web...", expanded=True) as status:
            # Extract a search-friendly name/topic from the URL
            if url_type == "linkedin_person":
                slug = url.rstrip("/").split("/")[-1].replace("-", " ")
                queries = [
                    f"{slug} professional background career",
                    f"{slug} recent news 2024 2025",
                ]
            else:
                # For company URLs, use the domain or LinkedIn slug
                slug = url.rstrip("/").split("/")[-1].replace("-", " ")
                queries = [
                    f"{slug} company overview products leadership",
                    f"{slug} recent news funding 2024 2025",
                ]

            search_results = []
            for q in queries:
                st.write(f"🔍 {q}")
                result = tavily.search(q, max_results=5, search_depth="basic")
                search_results.append(result)

            status.update(label="Writing briefing...", state="running")

            # --- Step 2: format search results for Claude ---
            research = ""
            for result in search_results:
                for r in result.get("results", []):
                    research += f"### {r['title']}\n{r['url']}\n{r['content']}\n\n"

            from datetime import datetime
            today = datetime.now().strftime("%B %d, %Y")
            context_line = f"\n\nMeeting context: {context}" if context else ""

            prompt = f"""Today is {today}. You are an executive research assistant preparing a pre-meeting briefing.

The meeting is regarding: {url}{context_line}

Here is fresh research gathered from the web:

{research}

Using this research, write a professional pre-meeting executive briefing with these exact sections:

# Pre-Meeting Executive Briefing

## Executive Summary
2–3 sentences: who/what this is and why the meeting matters.

## Background
- Current role/company or company overview
- Key history and milestones
- Leadership (if company)

## Recent News & Developments
- Key news from the research above (with approximate dates)

## Key Talking Points
- Topics they are focused on or publicly vocal about
- Likely priorities and pain points

## Suggested Questions to Ask
4–5 specific questions grounded in the research.

## Watch-Outs
- Anything sensitive, controversial, or worth handling carefully

---
*Briefing generated on {today}*"""

            # --- Step 3: Claude writes the briefing ---
            client = anthropic.Anthropic(api_key=anthropic_key)
            with client.messages.stream(
                model="claude-haiku-4-5",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                final = stream.get_final_message()

            status.update(label="Done!", state="complete", expanded=False)

        full_text = next(
            (block.text for block in final.content if block.type == "text"), ""
        )
        st.markdown(full_text)

    except anthropic.RateLimitError:
        st.error("Anthropic rate limit reached — please wait a minute and try again.")
    except anthropic.AuthenticationError:
        st.error("Invalid Anthropic API key. Check your Streamlit secrets.")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
