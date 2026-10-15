"""Email header parser — the other plain-Python agent tool.

Uses stdlib email parsing to surface the mismatches phishers rely on:
From vs Return-Path domains, Reply-To detours, and SPF/DKIM/DMARC
results from the Authentication-Results header.
"""
from __future__ import annotations

import email
import email.policy
import re
from email.utils import getaddresses


def _domain(addr: str) -> str:
    addr = (addr or "").strip()
    return addr.split("@")[-1].lower() if "@" in addr else ""


def parse_auth_results(auth: str) -> dict[str, str]:
    """Pull spf/dkim/dmarc verdicts out of Authentication-Results."""
    out: dict[str, str] = {}
    for mech in ("spf", "dkim", "dmarc"):
        m = re.search(rf"{mech}\s*=\s*(\w+)", auth or "", re.IGNORECASE)
        if m:
            out[mech] = m.group(1).lower()
    return out


def parse_headers(raw_email: str) -> dict:
    """Parse a raw RFC822 message; return a phishing-relevant summary."""
    msg = email.message_from_string(raw_email or "", policy=email.policy.default)

    from_addrs = [a for _, a in getaddresses(msg.get_all("From", []))]
    return_path = [a for _, a in getaddresses(msg.get_all("Return-Path", []))]
    reply_to = [a for _, a in getaddresses(msg.get_all("Reply-To", []))]

    from_domain = _domain(from_addrs[0]) if from_addrs else ""
    rp_domain = _domain(return_path[0]) if return_path else ""
    rt_domain = _domain(reply_to[0]) if reply_to else ""

    auth = " ".join(msg.get_all("Authentication-Results", []) or [])
    auth_verdicts = parse_auth_results(auth)

    flags: list[str] = []
    if from_domain and rp_domain and from_domain != rp_domain:
        flags.append(f"return-path-mismatch(from:{from_domain} vs bounce:{rp_domain})")
    if from_domain and rt_domain and rt_domain != from_domain:
        flags.append(f"reply-to-detour(reply-to:{rt_domain})")
    for mech in ("spf", "dkim", "dmarc"):
        v = auth_verdicts.get(mech)
        if v in ("fail", "softfail", "temperror", "permerror"):
            flags.append(f"{mech}-{v}")

    received = msg.get_all("Received", []) or []

    return {
        "from": from_addrs,
        "from_domain": from_domain,
        "return_path": return_path,
        "reply_to": reply_to,
        "subject": str(msg.get("Subject", "")),
        "date": str(msg.get("Date", "")),
        "auth": auth_verdicts,
        "received_hops": len(received),
        "flags": flags,
    }


def get_body_text(raw_email: str) -> str:
    """Best-effort plain-text body extraction for the agent to read."""
    msg = email.message_from_string(raw_email or "", policy=email.policy.default)
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        return ""
    return msg.get_content() if msg.get_content_type() == "text/plain" else ""


if __name__ == "__main__":
    sample = (
        "From: Billing <billing@paypal.com>\r\n"
        "Return-Path: <bounce@evil.example>\r\n"
        "Reply-To: support@evil.example\r\n"
        "Authentication-Results: spf=fail dmarc=fail\r\n"
        "Subject: Action required\r\n\r\n"
        "Click here to verify.\r\n"
    )
    import json
    print(json.dumps(parse_headers(sample), indent=2))
