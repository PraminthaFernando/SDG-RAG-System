from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextChunker:

    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, sentences: str) -> List[str]:
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap
        )
        
        chunks = text_splitter.split_text(sentences)
            
        return chunks