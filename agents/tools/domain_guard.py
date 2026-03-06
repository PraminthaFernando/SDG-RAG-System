from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    "un.org",
    "undp.org",
    "worldbank.org",
    "ipcc.ch"
]

def is_allowed(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        return any(domain.endswith(d) for d in ALLOWED_DOMAINS)
    except:
        return False