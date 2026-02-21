from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextChunker:

    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, sentences: str) -> List[str]:
        # chunks = []
        # current_chunk = []
        # current_length = 0
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap
        )
        
        chunks = text_splitter.split_text(sentences)

        # for sentence in sentences:
        #     if current_length + len(sentence) <= self.chunk_size:
        #         current_chunk.append(sentence)
        #         current_length += len(sentence)
        #     else:
        #         chunks.append(" ".join(current_chunk))

        #         # Overlap
        #         current_chunk = current_chunk[-self.overlap:] if self.overlap else []
        #         current_length = sum(len(s) for s in current_chunk)

        # if current_chunk:
        #     chunks.append(" ".join(current_chunk))
            
        return chunks