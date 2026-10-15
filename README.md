# DeskSentinel — AI IT Helpdesk & Phishing Triage Agent

A local AI agent that triages IT tickets and flags phishing emails —
running on consumer hardware, deployed live, with measured accuracy numbers.
The project a hiring manager can *click and try* in 30 seconds.

**Live demo:** _(push to a public Hugging Face Space and drop the link here)_

## Architecture

- **Local brain:** Qwen2.5-7B-Instruct at 4-bit quantization (~4.7 GB) via Ollama — fits an RTX 4060's 8 GB VRAM
- **Phishing classifier:** DistilBERT fine-tuned on a public phishing dataset from the HF Hub, with precision/recall/F1 on a held-out 20% split
- **Agent:** HF smolagents `CodeAgent` with custom tools — URL heuristics checker (homoglyph/TLD analysis), email header parser, KB search
- **Knowledge base:** small RAG index over security sources (CISA phishing indicators in `data/kb/`) with sentence-transformer embeddings
- **Demo:** free Hugging Face Space with a Gradio UI — paste an email, get verdict + explanation + suggested response draft

## Quickstart (Saturday morning)

```bash
# 1. Python 3.10+, then:
pip install -r requirements.txt

# 2. Ollama + the 7B model (needs ~5 GB disk, ~5 GB VRAM at Q4)
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Set DATASET_ID in desksentinel/classifier.py, then train (~30-60 min on GPU):
python -m desksentinel.classifier

# 4. Run the agent on a sample:
python -m desksentinel.agent

# 5. Launch the demo UI:
python -m desksentinel.app
```

## Project layout

```
desksentinel/
  tools/
    url_checker.py     # URL heuristics: IP hosts, homoglyphs, shorteners, bad TLDs
    header_parser.py   # From vs Return-Path, Reply-To detours, SPF/DKIM/DMARC
    kb_search.py       # tiny RAG over data/kb/
  classifier.py        # DistilBERT fine-tune on a Hub phishing dataset
  agent.py             # smolagents CodeAgent + Ollama wiring + triage_email()
  app.py               # Gradio demo UI (what ships to the Space)
data/kb/               # knowledge sources for the RAG index
tests/                 # stdlib-only smoke tests (run before pip install)
```

## Evaluation

| Component | Metric | Result |
|---|---|---|
| Phishing classifier (DistilBERT, held-out 20%) | F1 / Precision / Recall | _fill after training_ |
| Agent verdicts on 20 sample emails | Accuracy | _fill after eval_ |
| Local inference | Hardware | RTX 4060 8GB, Q4 quantization, no cloud cost |

## Ship it (Sunday)

```bash
huggingface-cli login
# create a Space at huggingface.co/spaces (SDK: Gradio), then:
git init && git add . && git commit -m "DeskSentinel v1"
git remote add space https://huggingface.co/spaces/<you>/desksentinel
git push space main
```

Then link the Space on your resume under this project.

## Roadmap

- LoRA fine-tune the 7B model itself on ticket/response pairs
- Frozen eval harness so every README number is reproducible
- Swap the LLM to HF Inference API for the Space demo if local latency is an issue
- Second use case: IT ticket priority classifier on synthetic tickets
