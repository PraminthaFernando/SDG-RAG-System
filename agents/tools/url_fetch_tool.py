from langchain_core.tools import tool
from .domain_guard import is_allowed
from .sanitizer import clean_html
import requests

@tool
def fetch_verified_url(url: str) -> str:
    """
    Fetch content from a verified SDG-related official URL.
    Only allowed domains will be processed.
    """

    if not is_allowed(url):
        return "Error: Domain not allowed."

    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "SDGComplianceAgent/1.0"}
        )
        if response.status_code != 200:
            return "Error: Failed to fetch content."
        return clean_html(response.text)

    except Exception:
        return "Error: Exception occurred during fetch."