# CISA — Phishing Indicators (starter notes)

Source: CISA "Phishing Guidance" — condensed working notes for DeskSentinel's KB.

## Common indicators

- Urgent or threatening language ("act now", "account suspended in 24 hours").
- Generic greetings ("Dear Customer") instead of your name.
- Sender address doesn't match the claimed organization; Reply-To points elsewhere.
- Links that look right but resolve to a different domain; hover-before-click.
- Unexpected attachments, especially .zip, .iso, .html, Office docs with macros.
- Requests for credentials, payment, or gift cards over email.

## Header tells

- Return-Path domain differs from the From domain.
- Authentication-Results shows spf=fail or dmarc=fail.
- Long Received chains with unfamiliar first hops.

## Handling guidance

- Don't click, don't reply, don't open attachments.
- Report to the security team / forward to the phishing mailbox.
- Verify out-of-band (call the sender at a known number) before acting on money or credential requests.
