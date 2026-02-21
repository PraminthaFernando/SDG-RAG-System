# ingestion/cleaner.py

import re
import spacy
from typing import List


class TextCleaner:

    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")

    def split_sentences(self, text: str) -> List[str]:
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents]

    def clean(self, sentences: List[str]) -> str:
        cleaned = ""

        for s in sentences:
            s = re.sub(r"\s+", " ", s)

            # Remove numeric-only lines
            if re.fullmatch(r"[\d\W]+", s):
                continue

            # Remove short fragments
            if len(s) < 20:
                continue

            cleaned += s + "\n"

        return cleaned