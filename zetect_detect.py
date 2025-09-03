# zetect_detect.py
import os
import re
import requests
from urllib.parse import urlparse
from html import unescape
from dotenv import load_dotenv
from openai import OpenAI
from zetect_auth import get_token  # device login for Graph

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"

# >>> EDIT THESE if you want allowlists <<<
SCHOOL_DOMAINS = {"wooster.edu"}  # you can leave as-is for testing
KNOWN_SAFE_LINK_DOMAINS = {
    "microsoft.com", "office.com", "outlook.com",
    "accounts.google.com", "github.com", "linkedin.com",
    "google.com", "zoom.us", "duo.com",
}
SUSPICIOUS_TLDS = {"ru", "tk", "top", "xyz", "click", "gq", "ml", "cf"}
URGENCY_PHRASES = {
    "verify your account", "urgent", "immediately",
    "update your password", "account suspended", "login now",
    "confirm your account", "act now", "reset your password",
    "payment required", "your mailbox is full"
}

# --- OpenAI setup ---
load_dotenv("zetect.env")  # load your API key from local file
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def fetch_messages(token, top=10):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "$top": top,
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,receivedDateTime,body,hasAttachments"
    }
    resp = requests.get(GRAPH_API_ENDPOINT, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("value", [])

def html_to_text(html):
    if not html:
        return ""
    html = re.sub(r"(?i)</(p|div|br|li|h[1-6])>", "\n", html)
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    text = re.sub(r"(?s)<[^>]+>", "", html)
    text = unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def extract_links(html):
    if not html:
        return []
    links = set()
    for m in re.finditer(r'(?is)<a[^>]+href\s*=\s*"([^"#]+)[^"]*"', html):
        links.add(m.group(1).strip())
    for m in re.finditer(r'(https?://[^\s<>"\)]+)', html):
        links.add(m.group(1).strip())
    return list(links)

def email_domain(address):
    if not address or "@" not in address:
        return ""
    return address.split("@", 1)[1].lower()

def url_domain(url):
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""

def domain_tld(domain):
    if "." not in domain:
        return ""
    return domain.rsplit(".", 1)[-1]

def score_message(sender_addr, body_html, subject, has_attachments):
    reasons = []
    score = 0

    sdom = email_domain(sender_addr)
    text = html_to_text(body_html)
    links = extract_links(body_html)

    # 1) Sender domain vs allowlist
    if sdom and sdom not in SCHOOL_DOMAINS:
        score += 1
        reasons.append(f"Sender domain not in allowlist: {sdom}")

    # 2) Urgency language
    lower_all = (subject or "").lower() + "\n" + text.lower()
    hits = [p for p in URGENCY_PHRASES if p in lower_all]
    if hits:
        score += 2
        reasons.append(f"Urgent language: {', '.join(sorted(hits)[:3])}")

    # 3) Link analysis
    if links:
        link_domains = {url_domain(u) for u in links if url_domain(u)}
        bad_tlds = [d for d in link_domains if domain_tld(d) in SUSPICIOUS_TLDS]
        if bad_tlds:
            score += 2
            reasons.append(f"Suspicious TLDs: {', '.join(sorted(set(bad_tlds)))}")
        mismatches = [
            d for d in link_domains
            if (sdom and d and (d != sdom)
                and not any(d.endswith(sd) for sd in (KNOWN_SAFE_LINK_DOMAINS | SCHOOL_DOMAINS)))
        ]
        if mismatches:
            score += 2
            reasons.append(f"Links to unrelated domains: {', '.join(sorted(set(mismatches)))}")

    # 4) Attachments (flag if from non-allowlist)
    if has_attachments and sdom not in SCHOOL_DOMAINS:
        score += 1
        reasons.append("Has attachment from non-allowlisted sender")

    # 5) Very short alarming subject
    if subject and len(subject) <= 6 and any(w in lower_all for w in ["urgent", "verify", "action"]):
        score += 1
        reasons.append("Short high-pressure subject")

    return score, reasons, text, links

def classify(score):
    if score >= 4:
        return "⚠️ Likely phishing"
    if score >= 2:
        return "❓ Suspicious"
    return "✅ Probably safe"

def classify_with_ai(subj, text):
    """Use OpenAI to classify email text."""
    if not client:
        return "(LLM disabled: no OPENAI_API_KEY loaded)"
    prompt = (
        "You are an email security assistant. "
        "Classify the email as 'phishing' or 'safe' and give a one-line reason.\n\n"
        f"Subject: {subj}\n\n"
        f"Body:\n{text[:2000]}"
    )
    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0
        )
        return resp.output[0].content[0].text.strip()
    except Exception as e:
        return f"(AI error: {e})"

def main():
    token = get_token()
    messages = fetch_messages(token, top=10)

    for i, m in enumerate(messages, start=1):
        subj = m.get("subject") or "(no subject)"
        sender = (m.get("from") or {}).get("emailAddress", {}).get("address", "(unknown)")
        date = m.get("receivedDateTime", "")
        body_obj = m.get("body") or {}
        body_ct = (body_obj.get("contentType") or "").lower()
        body_raw = body_obj.get("content") or ""
        has_att = bool(m.get("hasAttachments"))

        score, reasons, text_preview, links = score_message(sender, body_raw, subj, has_att)
        label = classify(score)

        # AI second opinion
        ai_label = classify_with_ai(subj, text_preview)

        preview = text_preview[:240].replace("\n", " ").strip()
        if len(text_preview) > 240:
            preview += "..."

        print(f"\n{i}. {label} (rules) | AI: {ai_label}")
        print(f"   Subject : {subj}")
        print(f"   From    : {sender}")
        print(f"   Date    : {date}")
        print(f"   Body    : {body_ct} ({len(body_raw)} chars)")
        print(f"   Preview : {preview}")
        if links:
            print(f"   Links   : {', '.join(links[:5])}" + (" ..." if len(links) > 5 else ""))
        if reasons:
            print(f"   Reasons : " + " | ".join(reasons))

if __name__ == "__main__":
    main()
