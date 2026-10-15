# DeskSentinel — AI IT Helpdesk & Phishing Triage Agent

**One-sentence pitch:** A local AI agent that triages IT tickets and flags phishing emails — running on consumer hardware, deployed live, with measured accuracy numbers. The project a hiring manager can *click and try* in 30 seconds.

**Why this one:** It sits exactly where the market is heading — IT/security work done with AI tooling. It demonstrates transformers, fine-tuning, agents, RAG, and deployment in one artifact. A Spaces demo link on a resume beats every bullet point.

---

## Architecture

- **Local brain:** Qwen2.5-7B-Instruct at Q4 quantization (~4.7 GB) via Ollama — fits your RTX 4060's 8 GB VRAM, best tool-calling in that bracket
- **Phishing classifier:** small transformer (e.g. DistilBERT) fine-tuned on a public phishing dataset from the HF Hub, with precision/recall on a held-out split — real numbers for the README
- **Agent:** HF smolagents CodeAgent with custom tools: URL heuristics checker (homoglyph/TLD analysis), email header parser, KB search
- **Knowledge base:** small RAG index over a handful of sources (CISA phishing indicators, your own IT playbook notes) with sentence-transformers embeddings
- **Demo:** free Hugging Face Space with a Gradio UI — paste an email, get a verdict + explanation + suggested response draft

## Weekend timeline

**Day 1 — brains (Sat)**
1. `pip install transformers torch huggingface-hub smolagents gradio datasets scikit-learn`
2. Install Ollama, `ollama pull qwen2.5:7b-instruct-q4_K_M` — confirm it runs on your GPU
3. Fine-tune the phishing classifier on a Hub dataset (search Hub datasets for "phishing" — pick one with 10k+ rows); train ~3 epochs, evaluate precision/recall/F1 on a held-out 20%
4. Build the two custom tools (URL checker, header parser) as plain Python functions first — test them standalone

**Day 2 — agent + ship (Sun)**
5. Wire smolagents CodeAgent: model = Ollama endpoint, tools = [url_checker, header_parser, kb_search, classifier]
6. RAG: embed 20–50 KB chunks with `sentence-transformers/all-MiniLM-L6-v2`, retrieve top-3 per query
7. Gradio UI: email in → verdict, confidence, indicators found, drafted response. Push to a public HF Space (`huggingface-cli login` first)
8. README: what it is, architecture diagram, eval table (classifier F1, agent success rate on 20 sample emails), hardware, how to run locally
9. Resume bullets (below) + LinkedIn post with the Space link

## Resume bullets (adapt freely)

- Built an AI helpdesk triage agent (Hugging Face smolagents, Qwen2.5-7B) that classifies phishing emails and suggests responses; deployed a live Gradio demo on Hugging Face Spaces
- Fine-tuned a transformer classifier on 10k+ phishing emails, achieving X% F1 on a held-out test set
- Implemented RAG over security knowledge bases with sentence-transformer embeddings for grounded, explainable verdicts
- Runs fully locally on a consumer RTX 4060 via 4-bit quantization — no cloud inference cost

## Companion credential (free)

Hugging Face's AI Agents Course — free, self-paced, includes a certificate. Pairs perfectly: course theory on the weeknights, this build on the weekend.

## Extensions (after the weekend)

- LoRA fine-tune the 7B model itself on ticket/response pairs
- Add an eval harness with a frozen task set so every README number is reproducible
- Swap the LLM to HF Inference API for the Space demo if local latency is an issue
- Second use case: IT ticket priority classifier trained on synthetic tickets — shows range

---
*Planned 2026-10-14. Hardware: RTX 4060 8GB. Stack: smolagents, transformers, Ollama, Gradio, Spaces.*
