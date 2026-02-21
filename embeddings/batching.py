from typing import List, Generator

def batch_iterable(items: List[str], batch_size: int) -> Generator[List[str], None, None]:
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]