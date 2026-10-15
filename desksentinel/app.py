"""Gradio demo UI — paste an email, get a verdict. This is what ships to the HF Space."""
from __future__ import annotations

import gradio as gr

from desksentinel.agent import triage_email

DEMO_EMAIL = """From: IT Support <it-support@yourcompany.com>
Reply-To: helpdesk@yourcompany-support.net
Subject: URGENT: Password expires today

Your password expires in 24 hours. Click here to keep your account active:
http://yourcompany-secure-login.tk/reset

- IT Department
"""


def triage(raw_email: str):
    result = triage_email(raw_email or DEMO_EMAIL)
    verdict = result.get("verdict", "suspicious").upper()
    conf = result.get("confidence", 50)
    indicators = result.get("indicators", [])
    explanation = result.get("explanation", "")
    response = result.get("suggested_response", "")

    summary = f"## Verdict: {verdict} ({conf}% confidence)\n\n{explanation}\n\n"
    summary += "### Indicators found\n"
    summary += "\n".join(f"- {i}" for i in indicators) or "- none"
    return summary, response


with gr.Blocks(title="DeskSentinel — AI Phishing Triage") as demo:
    gr.Markdown(
        "# 🛡️ DeskSentinel\n"
        "Paste a suspicious email below. The agent checks headers, URLs, "
        "a fine-tuned classifier, and a security knowledge base — then "
        "renders a verdict with a suggested response."
    )
    email_in = gr.Textbox(label="Raw email (headers + body)", lines=14,
                          placeholder="Paste the full email source here…", value=DEMO_EMAIL)
    go = gr.Button("Triage", variant="primary")
    verdict_out = gr.Markdown(label="Verdict")
    response_out = gr.Textbox(label="Suggested response", lines=8)
    go.click(triage, inputs=email_in, outputs=[verdict_out, response_out])

if __name__ == "__main__":
    demo.launch()
