import math
import re
from pathlib import Path
from typing import List, Dict, Tuple

class RAGIndex:
    def __init__(self):
        self.chunks = []
        self.doc_freqs = {}
        self.total_docs = 0
        self.avg_doc_len = 0
        self.doc_lengths = []
        self.tokenized_chunks = []
        
    def _tokenize(self, text: str) -> List[str]:
        # Simple lowercase alphanumeric tokenization
        return [w for w in re.split(r'\W+', text.lower()) if w]

    def build_index(self, folder_path: str, chunk_size_words: int = 200):
        """Scans a directory for text files and builds a BM25 index."""
        p = Path(folder_path).resolve()
        if not p.exists() or not p.is_dir():
            raise ValueError(f"Invalid directory: {folder_path}")
            
        allowed_extensions = {'.txt', '.md', '.py', '.json', '.yaml', '.yml', '.csv', '.sh'}
        
        all_text_chunks = []
        for file_path in p.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
                try:
                    # Ignore very large files for safety
                    if file_path.stat().st_size > 1024 * 1024 * 5: # 5MB
                        continue
                    text = file_path.read_text(errors="ignore")
                    words = text.split()
                    for i in range(0, len(words), chunk_size_words):
                        chunk = " ".join(words[i:i + chunk_size_words])
                        # Prepend file name for context
                        chunk_with_meta = f"File: {file_path.name}\n{chunk}"
                        all_text_chunks.append(chunk_with_meta)
                except Exception:
                    pass

        self._fit(all_text_chunks)
        
    def _fit(self, chunks: List[str]):
        self.chunks = chunks
        self.total_docs = len(chunks)
        if self.total_docs == 0:
            return
            
        total_len = 0
        for chunk in chunks:
            tokens = self._tokenize(chunk)
            self.tokenized_chunks.append(tokens)
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)
            
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                
        self.avg_doc_len = total_len / self.total_docs

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Returns the top_k most relevant chunks for the given query."""
        if self.total_docs == 0:
            return []
            
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
            
        scores = []
        k1 = 1.5
        b = 0.75
        
        for i, doc_tokens in enumerate(self.tokenized_chunks):
            score = 0.0
            doc_len = self.doc_lengths[i]
            
            # term frequencies in this document
            tf = {}
            for token in doc_tokens:
                tf[token] = tf.get(token, 0) + 1
                
            for token in query_tokens:
                if token not in self.doc_freqs:
                    continue
                
                # IDF
                df = self.doc_freqs[token]
                idf = math.log(1 + (self.total_docs - df + 0.5) / (df + 0.5))
                
                # TF component
                f = tf.get(token, 0)
                numerator = f * (k1 + 1)
                denominator = f + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
                
                score += idf * (numerator / denominator)
                
            scores.append((score, self.chunks[i]))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scores[:top_k] if score > 0]

