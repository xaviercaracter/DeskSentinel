"""URL heuristics checker — one of DeskSentinel's plain-Python agent tools.

Catches the cheap, high-signal phishing URL tricks without any ML:
IP-literal hosts, @ tricks, punycode/homoglyphs, URL shorteners,
suspicious TLDs, and excessive subdomain depth.
"""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s<>\"]+|www\.[^\s<>\"]+", re.IGNORECASE)

# Common Cyrillic/Greek lookalikes for ASCII letters (a minimal homoglyph map)
HOMOGLYPHS = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "у": "y", "і": "i", "ј": "j", "ѕ": "s", "ԝ": "w", "ԛ": "q",
    "τ": "t", "ν": "v", "κ": "k", "μ": "m", "ο": "o", "ρ": "p",
}

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "shorte.st", "rebrand.ly", "cutt.ly",
}

SUSPICIOUS_TLDS = {
    ".zip", ".mov", ".click", ".link", ".top", ".xyz", ".tk",
    ".ml", ".ga", ".cf", ".gq", ".cam", ".rest", ".review",
}


def extract_urls(text: str) -> list[str]:
    """Pull candidate URLs out of raw email text."""
    urls = URL_RE.findall(text or "")
    # strip trailing punctuation the regex can swallow
    return [u.rstrip(".,;:!?)") for u in urls]


def has_homoglyph(host: str) -> tuple[bool, str]:
    """Return (found, deceptive_form) for mixed-script lookalikes in the host."""
    suspicious = [c for c in host if c in HOMOGLYPHS]
    if suspicious:
        deceptive = "".join(HOMOGLYPHS.get(c, c) for c in host)
        return True, deceptive
    return False, host


def check_url(url: str) -> dict:
    """Score a single URL. Higher 'score' = more suspicious."""
    parsed = urlparse(url if "://" in url else "http://" + url)
    host = (parsed.hostname or "").lower()
    flags: list[str] = []
    score = 0

    try:
        ipaddress.ip_address(host)
        flags.append("host-is-ip-literal")
        score += 3
    except ValueError:
        pass

    if "@" in (parsed.netloc or ""):
        flags.append("credential-redirect-trick(@)")
        score += 3

    if host.startswith("xn--") or any(part.startswith("xn--") for part in host.split(".")):
        flags.append("punycode-idn")
        score += 2

    homo, deceptive = has_homoglyph(host)
    if homo:
        flags.append(f"homoglyph-lookalike(looks-like:{deceptive})")
        score += 3

    if host in SHORTENERS or any(host.endswith("." + s) for s in SHORTENERS):
        flags.append("url-shortener-hides-destination")
        score += 2

    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        flags.append("suspicious-tld")
        score += 2

    depth = len([p for p in host.split(".") if p])
    if depth >= 4 and "host-is-ip-literal" not in flags:
        flags.append(f"deep-subdomain-chain({depth} labels)")
        score += 1

    return {"url": url, "host": host, "flags": flags, "score": score}


def check_urls(text: str) -> list[dict]:
    """Scan email text; return per-URL findings, worst first."""
    results = [check_url(u) for u in extract_urls(text)]
    return sorted(results, key=lambda r: r["score"], reverse=True)


if __name__ == "__main__":
    sample = "Hi, verify at http://192.168.1.1/login or https://аpple.com.verify.zip/secure"
    for r in check_urls(sample):
        print(r)
