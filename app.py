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

    full_text = ""
    search_count = 0

    with st.status("Researching — this takes about 30 seconds...", expanded=True) as status:
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
            current_block_type = None
            current_query_parts = []

            for event in stream:
                etype = getattr(event, "type", None)

                if etype == "content_block_start":
                    block = event.content_block
                    current_block_type = block.type
                    if block.type == "server_tool_use":
                        current_query_parts = []

                elif etype == "content_block_delta":
                    delta = event.delta
                    dtype = getattr(delta, "type", None)

                    if dtype == "input_json_delta" and current_block_type == "server_tool_use":
                        current_query_parts.append(getattr(delta, "partial_json", ""))

                    elif dtype == "text_delta":
                        full_text += delta.text

                elif etype == "content_block_stop":
                    if current_block_type == "server_tool_use" and current_query_parts:
                        import json
                        raw = "".join(current_query_parts)
                        try:
                            query = json.loads(raw).get("query") or json.loads(raw).get("url", raw)
                        except Exception:
                            query = raw
                        if query:
                            search_count += 1
                            st.write(f"🔍 {query}")
                    current_block_type = None
                    current_query_parts = []

        status.update(
            label=f"Done — {search_count} searches completed",
            state="complete",
            expanded=False,
        )

    st.markdown(full_text)
