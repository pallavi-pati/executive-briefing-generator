# Executive Meeting Briefing Generator

CLI tool that takes a LinkedIn profile or company URL and generates a structured pre-meeting briefing using Claude AI with live web search.

## What it generates

- **Executive Summary** — who they are and why the meeting matters
- **Background** — career history, company overview, leadership
- **Recent News** — last 6 months of press, announcements, activity
- **Key Talking Points** — topics they care about, conversation starters
- **Suggested Questions** — grounded in actual research
- **Watch-Outs** — red flags or sensitive topics to avoid

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY='sk-ant-...'
```

## Usage

```bash
# LinkedIn person profile
python briefing.py https://linkedin.com/in/satyanadella

# LinkedIn company page
python briefing.py https://linkedin.com/company/openai

# Any company website
python briefing.py https://stripe.com

# With meeting context and save to file
python briefing.py https://stripe.com -c "Evaluating as a payments vendor" -o stripe_briefing.md
```

## How it works

Sends the URL to **Claude Opus 4.6** with access to Anthropic's server-side web search and web fetch tools. Claude searches for recent news, fetches relevant pages, and synthesizes everything into a structured briefing. The full research and writing process streams to your terminal in real time.

## Requirements

- Python 3.9+
- `anthropic` Python SDK (`pip install anthropic`)
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))
