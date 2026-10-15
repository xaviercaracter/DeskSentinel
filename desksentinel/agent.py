"""Wire the smolagents CodeAgent: Ollama-hosted Qwen2.5-7B + DeskSentinel tools.

Prereqs: `ollama pull qwen2.5:7b-instruct-q4_K_M` and Ollama serving
on http://localhost:11434 (default).

triage_email(raw_email) -> dict with verdict, confidence, indicators,
and a suggested analyst response — the 30-second demo moment.
"""
from __future__ import annotations

from smolagents import CodeAgent, OpenAIServerModel, tool

from .tools.header_parser import get_body_text, parse_headers
from .tools.kb_search import KBSearch
from .tools.url_checker import check_urls


@tool
def analyze_headers(raw_email: str) -> str:
    """Parse email headers and return phishing-relevant findings as text."""
    import json

    return json.dumps(parse_headers(raw_email), indent=2)


@tool
def analyze_urls(raw_email: str) -> str:
    """Extract URLs from the email body and flag suspicious ones."""
    import json

    body = get_body_text(raw_email)
    return json.dumps(check_urls(raw_email + "\n" + body), indent=2)


@tool
def search_knowledge_base(query: str) -> str:
    """Look up known phishing indicators and handling guidance."""
    import json

    kb = KBSearch()
    return json.dumps(kb.search(query, top_k=3), indent=2)


@tool
def classify_with_model(text: str) -> str:
    """Run the fine-tuned phishing classifier on the email text.

    Loads ./classifier-out if present, else falls back to a zero-shot
    pipeline so the agent still works before Saturday's training run.
    """
    from pathlib import Path

    text = text[:2000]
    if Path("classifier-out").exists():
        from transformers import pipeline

        clf = pipeline("text-classification", model="classifier-out")
        out = clf(text)[0]
        return f"{out['label']} (score={out['score']:.3f}) [fine-tuned]"
    from transformers import pipeline

    clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    out = clf(text, candidate_labels=["phishing", "legitimate"])
    return f"{out['labels'][0]} (score={out['scores'][0]:.3f}) [zero-shot fallback]"


SYSTEM_PROMPT = """You are DeskSentinel, an AI IT helpdesk triage agent.
For each email: call the tools, weigh the evidence, then return your
final answer as JSON with keys: verdict ("phishing" | "legitimate" |
"suspicious"), confidence (0-100), indicators (list of strings),
explanation (2-3 sentences), suggested_response (a short draft reply
or analyst note). Cite which tool produced each indicator."""


def build_agent() -> CodeAgent:
    model = OpenAIServerModel(
        model_id="qwen2.5:7b-instruct",
        api_base="http://localhost:11434/v1",
        api_key="ollama",  # Ollama ignores the key
    )
    return CodeAgent(
        tools=[analyze_headers, analyze_urls, search_knowledge_base, classify_with_model],
        model=model,
        add_base_tools=False,
    )


def triage_email(raw_email: str) -> dict:
    import json

    agent = build_agent()
    result = agent.run(
        f"{SYSTEM_PROMPT}\n\nTriage this email:\n{raw_email[:4000]}"
    )
    try:
        return json.loads(result) if isinstance(result, str) else dict(result)
    except Exception:
        return {"verdict": "suspicious", "confidence": 50,
                "indicators": ["agent output was not valid JSON"],
                "explanation": str(result)[:500],
                "suggested_response": "Escalate to a human analyst for review."}


if __name__ == "__main__":
    demo = "Subject: Urgent: verify your account\n\nClick https://bit.ly/xyz123 to verify now."
    import json
    print(json.dumps(triage_email(demo), indent=2))
