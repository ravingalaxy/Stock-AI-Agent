"""News & Sentiment Agent - Collects and analyzes news flow."""

import json
from typing import Dict, Any, List
from datetime import date, timedelta

from src.utils.logger import logger
from src.data.news_collector import (
    collect_news_for_symbol, process_raw_articles
)
from src.llm.llm_client import get_llm_client
from src.llm.prompts import FINANCIAL_ANALYST_SYSTEM, NEWS_AGENT_PROMPT
from src.llm.schemas import NewsAnalysisOutput
from src.storage.database import StockRepository
from src.storage.vector_store import get_vector_store


class NewsAgent:
    """Collects, processes, and analyzes news for sentiment and catalysts."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.llm = get_llm_client()
        self.vector_store = get_vector_store()
        
    def analyze(self, symbol: str, days: int = 30, limit: int = 20) -> Dict[str, Any]:
        """Run complete news analysis."""
        logger.info(f"Running news analysis for {symbol}")
        
        # 1. Get company name
        stock = self.repo.get_stock(symbol)
        company_name = stock.name if stock else symbol
        
        # 2. Collect news
        raw_articles = collect_news_for_symbol(symbol, company_name, days=days, limit=limit*2)
        
        if not raw_articles:
            return self._empty_result(symbol)
            
        # 3. Store in vector DB for semantic search
        self._store_in_vector_db(symbol, raw_articles)
        
        # 4. Prepare for LLM (limit tokens)
        articles_for_llm = raw_articles[:limit]
        
        # 5. LLM Analysis
        qualitative = self._run_llm_analysis(symbol, company_name, articles_for_llm)
        
        # 6. Compute aggregate metrics
        aggregate = self._compute_aggregates(raw_articles, qualitative)
        
        return {
            "symbol": symbol,
            "article_count": len(raw_articles),
            "articles": raw_articles[:10],  # Store top 10 in result
            "aggregate_metrics": aggregate,
            "qualitative_analysis": qualitative,
            "analyzed_at": date.today().isoformat()
        }
    
    def _store_in_vector_db(self, symbol: str, articles: List[Dict]):
        """Store articles in vector database for semantic search."""
        import hashlib

        texts = []
        metadatas = []
        ids = []
        
        for idx, art in enumerate(articles):
            text = f"{art.get('title', '')}. {art.get('summary', '')}"
            if len(text.strip()) < 50:
                continue
                
            texts.append(text)
            metadatas.append({
                "symbol": symbol,
                "doc_type": "news",
                "source_url": art.get("url", ""),
                "published_at": art.get("published_at", "").isoformat() if hasattr(art.get("published_at"), "isoformat") else str(art.get("published_at", "")),
                "title": art.get("title", "")[:500],
                "publisher": art.get("publisher", "")[:100],
            })
            url_part = art.get('url', '')
            url_hash = hashlib.md5(url_part.encode('utf-8', errors='ignore')).hexdigest()[:12] if url_part else str(idx)
            ids.append(f"{symbol}_news_{idx}_{url_hash}")
            
        if texts:
            self.vector_store.add_documents(texts, metadatas, ids)
    
    def _compute_aggregates(self, articles: List[Dict], qualitative: Dict) -> Dict[str, Any]:
        """Compute aggregate sentiment and event metrics."""
        if not articles:
            return {}
            
        sentiments = [a.get("sentiment_score", 0) for a in articles]
        relevances = [a.get("relevance_score", 0) for a in articles]
        
        # Weight by relevance
        weighted_sentiment = sum(s * r for s, r in zip(sentiments, relevances))
        total_relevance = sum(relevances)
        avg_sentiment = weighted_sentiment / total_relevance if total_relevance > 0 else 0
        
        # Count events
        all_events = []
        for a in articles:
            all_events.extend(a.get("events", []))
            
        from collections import Counter
        event_counts = Counter(all_events)
        
        return {
            "avg_sentiment": round(avg_sentiment, 3),
            "avg_relevance": round(sum(relevances) / len(relevances), 3) if relevances else 0,
            "article_count": len(articles),
            "positive_count": len([a for a in articles if a.get("sentiment_score", 0) > 0.1]),
            "negative_count": len([a for a in articles if a.get("sentiment_score", 0) < -0.1]),
            "neutral_count": len([a for a in articles if -0.1 <= a.get("sentiment_score", 0) <= 0.1]),
            "events_detected": list(event_counts.keys()),
            "event_counts": dict(event_counts),
            "latest_news_days_ago": qualitative.get("latest_news_days_ago", 999)
        }
    
    def _run_llm_analysis(self, symbol: str, company_name: str, articles: List[Dict]) -> Dict[str, Any]:
        """Run LLM qualitative news analysis."""
        try:
            prompt = NEWS_AGENT_PROMPT.format(
                symbol=symbol,
                company_name=company_name,
                articles_json=json.dumps(articles, indent=2, default=str)
            )
            
            messages = [
                {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm.chat_structured(
                messages=messages,
                response_model=NewsAnalysisOutput
            )
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM news analysis failed for {symbol}: {e}")
            return {"error": str(e), "overall_sentiment": "Unknown"}
    
    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "article_count": 0,
            "articles": [],
            "aggregate_metrics": {},
            "qualitative_analysis": {"error": "No news available"},
            "analyzed_at": date.today().isoformat()
        }
    
    def search_semantic(self, symbol: str, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search on stored news."""
        return self.vector_store.similarity_search(query, symbol=symbol, top_k=top_k)