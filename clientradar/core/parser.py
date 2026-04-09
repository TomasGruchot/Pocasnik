from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


class DataParser:
    _EMAIL_RE = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )

    _BLACKLISTED_DOMAINS = {
        "sentry.io", "wixpress.com", "example.com",
        "domain.com", "email.com", "change.me",
    }

    def clean_phone(self, raw: str) -> str:
        if not raw:
            return ""
        digits = re.sub(r"[^\d+]", "", raw)
        if digits.startswith("00420"):
            digits = "+" + digits[2:]
        elif digits.startswith("420") and len(digits) >= 12:
            digits = "+" + digits
        elif len(digits) == 9 and digits[0] in "2367":
            digits = "+420" + digits
        parts = []
        clean = digits.lstrip("+")
        prefix = "+" if digits.startswith("+") else ""
        if prefix and len(clean) >= 12:
            parts = [prefix + clean[:3], clean[3:6], clean[6:9], clean[9:]]
        elif len(clean) == 9:
            parts = [clean[:3], clean[3:6], clean[6:]]
        else:
            return digits
        return " ".join(p for p in parts if p)

    def extract_email_from_website(self, url: str) -> str:
        if not url or not url.startswith("http"):
            return ""
        try:
            resp = requests.get(
                url,
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"},
                allow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            mailto_tag = soup.select_one('a[href^="mailto:"]')
            if mailto_tag:
                email = mailto_tag["href"].replace("mailto:", "").split("?")[0].strip()
                if self._is_valid_email(email):
                    return email

            all_emails = self._EMAIL_RE.findall(resp.text)
            for email in all_emails:
                if self._is_valid_email(email):
                    return email
        except Exception:
            pass
        return ""

    def _is_valid_email(self, email: str) -> bool:
        if not email or "@" not in email:
            return False
        domain = email.split("@")[1].lower()
        if domain in self._BLACKLISTED_DOMAINS:
            return False
        if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
            return False
        return True

    def normalize_rating(self, raw: str) -> float:
        if not raw:
            return 0.0
        try:
            cleaned = raw.replace(",", ".").strip()
            cleaned = re.sub(r"[^\d.]", "", cleaned)
            return round(float(cleaned), 1)
        except (ValueError, TypeError):
            return 0.0

    def parse_review_count(self, raw: str) -> int:
        if not raw:
            return 0
        try:
            digits = re.sub(r"[^\d]", "", raw)
            return int(digits) if digits else 0
        except (ValueError, TypeError):
            return 0
