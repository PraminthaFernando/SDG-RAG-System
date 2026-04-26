from tenacity import retry, stop_after_attempt, wait_exponential

def retry_llm():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10)
    )