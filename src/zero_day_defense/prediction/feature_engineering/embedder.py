"""LLM embedder for semantic features."""
from __future__ import annotations

import os
from typing import List, Optional

import numpy as np

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from ..models import CommitSignal, PRSignal, IssueSignal
from ..exceptions import EmbeddingError


class LLMEmbedder:
    """Generate semantic embeddings using LLM (Gemini API)."""
    
    def __init__(
        self,
        model: str = "models/text-embedding-004",
        api_key: Optional[str] = None,
    ):
        """Initialize embedder.
        
        Args:
            model: Gemini embedding model name
            api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
            
        Raises:
            EmbeddingError: If google-generativeai library is not installed
        """
        if genai is None:
            raise EmbeddingError(
                "google-generativeai library not installed. Run: pip install google-generativeai"
            )
        
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise EmbeddingError(
                "Gemini API key not provided. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        genai.configure(api_key=self.api_key)
    
    def embed_commit_messages(
        self,
        commits: List[CommitSignal],
        max_length: int = 8000,
    ) -> np.ndarray:
        """Generate embeddings for commit messages.
        
        Args:
            commits: List of CommitSignal objects
            max_length: Maximum text length for embedding
            
        Returns:
            Aggregated embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not commits:
            raise EmbeddingError("No commits provided for embedding")
        
        # Combine commit messages
        messages = [c.message for c in commits]
        combined_text = " ".join(messages)[:max_length]
        
        return self._get_embedding(combined_text)
    
    def embed_pr_descriptions(
        self,
        prs: List[PRSignal],
        max_length: int = 8000,
    ) -> np.ndarray:
        """Generate embeddings for PR titles and descriptions.
        
        Args:
            prs: List of PRSignal objects
            max_length: Maximum text length for embedding
            
        Returns:
            Aggregated embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not prs:
            raise EmbeddingError("No PRs provided for embedding")
        
        # Combine PR titles and descriptions
        texts = [f"{pr.title} {pr.description}" for pr in prs]
        combined_text = " ".join(texts)[:max_length]
        
        return self._get_embedding(combined_text)
    
    def embed_issue_discussions(
        self,
        issues: List[IssueSignal],
        max_length: int = 8000,
    ) -> np.ndarray:
        """Generate embeddings for issue discussions.
        
        Args:
            issues: List of IssueSignal objects
            max_length: Maximum text length for embedding
            
        Returns:
            Aggregated embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not issues:
            raise EmbeddingError("No issues provided for embedding")
        
        # Combine issue titles, bodies, and first few comments
        texts = []
        for issue in issues:
            text = f"{issue.title} {issue.body}"
            # Add first 3 comments
            if issue.comments:
                text += " " + " ".join(issue.comments[:3])
            texts.append(text)
        
        combined_text = " ".join(texts)[:max_length]
        
        return self._get_embedding(combined_text)
    
    def aggregate_embeddings(
        self,
        embeddings: List[np.ndarray],
        method: str = "mean",
    ) -> np.ndarray:
        """Aggregate multiple embeddings into one vector.
        
        Args:
            embeddings: List of embedding vectors
            method: Aggregation method (mean, max, sum)
            
        Returns:
            Aggregated embedding vector
            
        Raises:
            EmbeddingError: If aggregation fails
        """
        if not embeddings:
            raise EmbeddingError("No embeddings provided for aggregation")
        
        embeddings_array = np.array(embeddings)
        
        if method == "mean":
            return np.mean(embeddings_array, axis=0)
        elif method == "max":
            return np.max(embeddings_array, axis=0)
        elif method == "sum":
            return np.sum(embeddings_array, axis=0)
        else:
            raise EmbeddingError(f"Unknown aggregation method: {method}")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text string using Gemini API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If API call fails
        """
        if not text or not text.strip():
            raise EmbeddingError("Empty text provided for embedding")
        
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document",
            )
            embedding = result['embedding']
            return np.array(embedding)
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {e}")
