import streamlit as st
import anthropic
from briefing import build_prompt, detect_url_type

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
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        st.error("ANTHROPIC_API_KEY not found in Streamlit secrets.")
        st.stop()

    client = anthropic.Anthropic(api_key=api_key)
    url_type = detect_url_type(url)
    prompt = build_prompt(url, url_type, context)

    try:
        with st.spinner("Researching via web search — this takes about 30–60 seconds..."):
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=8000,
                tools=[
                    {"type": "web_search_20260209", "name": "web_search"},
                    {"type": "web_fetch_20260209", "name": "web_fetch"},
                ],
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                final = stream.get_final_message()

        full_text = next(
            (block.text for block in final.content if block.type == "text"), ""
        )
        st.markdown(full_text)

    except anthropic.RateLimitError:
        st.error("Rate limit reached — please wait a minute and try again.")
    except anthropic.AuthenticationError:
        st.error("Invalid API key. Check your Streamlit secrets.")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
