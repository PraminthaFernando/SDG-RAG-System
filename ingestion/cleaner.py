# ingestion/cleaner.py

import re
import spacy
import time
from typing import List


class TextCleaner:

    def __init__(self):
        print("🧠 [Cleaner] Initializing TextCleaner...")
        t0 = time.time()

        print("🧠 [Cleaner] Loading spaCy model: en_core_web_sm")
        self.nlp = spacy.load("en_core_web_sm")

        print(f"✅ [Cleaner] spaCy model loaded in {round(time.time() - t0, 2)}s")

    def split_sentences(self, text: str) -> List[str]:
        start = time.time()

        print(f"\n✂️ [Cleaner] Splitting sentences | text length = {len(text)}")

        doc = self.nlp(text)

        sentences = [sent.text.strip() for sent in doc.sents]

        print(f"✅ [Cleaner] Extracted {len(sentences)} sentences in {round(time.time() - start, 2)}s")

        return sentences

    def clean(self, sentences: List[str]) -> str:
        start = time.time()

        print(f"\n🧹 [Cleaner] Cleaning {len(sentences)} sentences")

        cleaned = ""

        for i, s in enumerate(sentences, 1):
            cleaned += s + "\n"

            # Optional progress log every 100 sentences
            if i % 100 == 0:
                print(f"   🔄 Processed {i} sentences...")

        print(f"✅ [Cleaner] Cleaned text length = {len(cleaned)} in {round(time.time() - start, 2)}s")

        return cleaned