"""Search engine with fuzzy matching."""

import re
from difflib import SequenceMatcher
from typing import Optional

from .snippet import Snippet


class SearchEngine:
    """Fuzzy search for snippets."""
    
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
    
    def fuzzy_match(self, text: str, query: str) -> float:
        """Calculate fuzzy match score."""
        if not text or not query:
            return 0.0
        
        text_lower = text.lower()
        query_lower = query.lower()
        
        if query_lower in text_lower:
            return 1.0
        
        words = query_lower.split()
        scores = []
        for word in words:
            if word in text_lower:
                scores.append(1.0)
            else:
                score = SequenceMatcher(None, word, text_lower).ratio()
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def search(self, snippets: list[Snippet], query: str, language: Optional[str] = None, tags: Optional[list[str]] = None) -> list[tuple[Snippet, float]]:
        """Search snippets with fuzzy matching."""
        if not query and not language and not tags:
            return [(s, 1.0) for s in snippets]
        
        results = []
        
        for snippet in snippets:
            score = 0.0
            
            if language:
                if snippet.language.lower() == language.lower():
                    score += 0.3
            
            if tags:
                tag_match = sum(1 for t in tags if t.lower() in [tag.lower() for tag in snippet.tags])
                if tag_match > 0:
                    score += 0.2 * (tag_match / len(tags))
            
            if query:
                title_score = self.fuzzy_match(snippet.title, query) * 0.4
                desc_score = self.fuzzy_match(snippet.description, query) * 0.2
                code_score = self.fuzzy_match(snippet.code, query) * 0.3
                tag_score = self.fuzzy_match(" ".join(snippet.tags), query) * 0.1
                score += title_score + desc_score + code_score + tag_score
            
            if score > 0:
                results.append((snippet, min(score, 1.0)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def highlight_match(self, text: str, query: str) -> str:
        """Return text with matched portions highlighted."""
        if not query:
            return text
        
        pattern = re.escape(query)
        return re.sub(f"({pattern})", "**\\1**", text, flags=re.IGNORECASE)
