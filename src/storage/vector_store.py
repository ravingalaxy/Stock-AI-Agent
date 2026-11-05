"""Vector Store wrapper using ChromaDB for semantic search on news and filings."""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings

from src.utils.logger import logger


class VectorStoreManager:
    """Manages ChromaDB vector collections for document embeddings."""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection_name = "news_and_filings"
        self.collection = self._get_or_create_collection()
        
    def _get_or_create_collection(self):
        """Get or create the document collection."""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
    def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]], 
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents with embeddings to the vector store.
        
        Args:
            texts: List of document texts to embed.
            metadatas: List of metadata dicts (must include 'symbol', 'doc_type', 'source_url', 'published_at').
            ids: Optional list of unique IDs. Auto-generated if not provided.
            
        Returns:
            List of document IDs.
        """
        if not texts:
            return []
            
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
            
        # Ensure metadata has required fields
        validated_metadatas = []
        for meta in metadatas:
            validated = {
                "symbol": meta.get("symbol", "UNKNOWN"),
                "doc_type": meta.get("doc_type", "news"),
                "source_url": meta.get("source_url", ""),
                "published_at": meta.get("published_at", datetime.utcnow().isoformat()),
                "title": meta.get("title", "")[:500],
                "publisher": meta.get("publisher", "")[:100],
            }
            validated_metadatas.append(validated)
            
        # Deduplicate within the batch while ensuring unique IDs
        unique_texts = []
        unique_metadatas = []
        unique_ids = []
        seen_ids = set()

        for t, m, doc_id in zip(texts, validated_metadatas, ids):
            curr_id = str(doc_id)
            counter = 1
            while curr_id in seen_ids:
                curr_id = f"{doc_id}_{counter}"
                counter += 1
            seen_ids.add(curr_id)
            unique_texts.append(t)
            unique_metadatas.append(m)
            unique_ids.append(curr_id)

        try:
            # Use upsert to handle both new and existing documents safely
            if hasattr(self.collection, "upsert"):
                self.collection.upsert(
                    documents=unique_texts,
                    metadatas=unique_metadatas,
                    ids=unique_ids
                )
            else:
                self.collection.add(
                    documents=unique_texts,
                    metadatas=unique_metadatas,
                    ids=unique_ids
                )
            logger.info(f"Upserted {len(unique_texts)} documents to vector store.")
            return unique_ids
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            return []
            
    def similarity_search(
        self, 
        query: str, 
        symbol: Optional[str] = None,
        doc_type: Optional[str] = None,
        top_k: int = 5,
        date_from: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search.
        
        Args:
            query: Search query text.
            symbol: Filter by stock symbol.
            doc_type: Filter by document type ('news', 'filing', 'presentation').
            top_k: Number of results to return.
            date_from: ISO format date string filter (documents after this date).
            
        Returns:
            List of result dicts with text, metadata, and similarity score.
        """
        where_filter = {}
        if symbol:
            where_filter["symbol"] = symbol
        if doc_type:
            where_filter["doc_type"] = doc_type
        # Note: Chroma where filter doesn't natively support date range on string dates easily
        # We'll do post-filtering if needed
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            output = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance  # cosine similarity
                    
                    # Post-filter by date if provided
                    if date_from:
                        doc_date = metadata.get("published_at", "")
                        if doc_date < date_from:
                            continue
                            
                    output.append({
                        "text": doc,
                        "metadata": metadata,
                        "similarity": similarity,
                        "distance": distance
                    })
            return output
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
            
    def get_symbol_documents(self, symbol: str, doc_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve all documents for a specific symbol (for agent context)."""
        where_filter = {"symbol": symbol}
        if doc_type:
            where_filter["doc_type"] = doc_type
            
        try:
            results = self.collection.get(
                where=where_filter,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            output = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    output.append({
                        "text": doc,
                        "metadata": results["metadatas"][i]
                    })
            return output
        except Exception as e:
            logger.error(f"Failed to retrieve symbol documents: {e}")
            return []
            
    def delete_symbol_documents(self, symbol: str) -> bool:
        """Delete all documents for a symbol (useful for refresh)."""
        try:
            self.collection.delete(where={"symbol": symbol})
            logger.info(f"Deleted all documents for {symbol} from vector store.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete symbol documents: {e}")
            return False
            
    def count(self) -> int:
        """Return total document count."""
        return self.collection.count()


# Global instance
_vector_store: Optional[VectorStoreManager] = None

def get_vector_store(persist_directory: str = "data/chroma_db") -> VectorStoreManager:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager(persist_directory)
    return _vector_store