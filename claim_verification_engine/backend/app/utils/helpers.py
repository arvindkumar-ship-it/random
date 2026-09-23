from typing import Optional
import re


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        domain = url.split('/')[2]
        return domain.lower()
    except Exception:
        return None


def sanitize_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r"[^\w\s\.\,\!\?\-\']", '', text)
    return text.strip()
