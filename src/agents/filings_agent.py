"""Filings & Disclosure Agent - Corporate announcements and governance analysis."""

import json
from typing import Dict, Any, List
from datetime import date

from src.utils.logger import logger
from src.data.filings_collector import collect_filings_for_symbol
from src.llm.llm_client import get_llm_client
from src.llm.prompts import FINANCIAL_ANALYST_SYSTEM, FILINGS_AGENT_PROMPT
from src.llm.schemas import FilingsAnalysisOutput
from src.storage.database import StockRepository
from src.storage.vector_store import get_vector_store


class FilingsAgent:
    """Analyzes corporate filings, shareholding, and governance."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.llm = get_llm_client()
        self.vector_store = get_vector_store()
        
    def analyze(self, symbol: str, days: int = 90) -> Dict[str, Any]:
        """Run complete filings analysis."""
        logger.info(f"Running filings analysis for {symbol}")
        
        # 1. Get company name
        stock = self.repo.get_stock(symbol)
        company_name = stock.name if stock else symbol
        
        # 2. Collect filings
        filings_data = collect_filings_for_symbol(symbol, days=days)
        
        if not filings_data.get("announcements"):
            return self._empty_result(symbol)
            
        # 3. Store in vector DB
        self._store_in_vector_db(symbol, filings_data)
        
        # 4. LLM Analysis
        qualitative = self._run_llm_analysis(symbol, company_name, filings_data)
        
        # 5. Extract key structured flags
        structured_flags = self._extract_structured_flags(filings_data)
        
        return {
            "symbol": symbol,
            "announcements_count": len(filings_data.get("announcements", [])),
            "categorized": filings_data.get("categorized", {}),
            "shareholding": filings_data.get("shareholding"),
            "presentations": filings_data.get("presentations", []),
            "structured_flags": structured_flags,
            "qualitative_analysis": qualitative,
            "analyzed_at": date.today().isoformat()
        }
    
    def _store_in_vector_db(self, symbol: str, filings_data: Dict):
        """Store filings in vector database."""
        texts = []
        metadatas = []
        ids = []
        
        for idx, ann in enumerate(filings_data.get("announcements", [])):
            text = f"{ann.get('subject', '')}. {ann.get('description', '')}"
            if len(text.strip()) < 50:
                continue
                
            texts.append(text)
            metadatas.append({
                "symbol": symbol,
                "doc_type": "filing",
                "source_url": ann.get("attachment_url", ""),
                "published_at": ann.get("published_at", "").isoformat() if hasattr(ann.get("published_at"), "isoformat") else str(ann.get("published_at", "")),
                "title": ann.get("subject", "")[:500],
                "publisher": "NSE",
            })
            # Use index to ensure unique IDs even with same subject
            subject_suffix = ann.get('subject', '')[-50:] if ann.get('subject') else 'unknown'
            ids.append(f"{symbol}_filing_{idx}_{subject_suffix}")
            
        if texts:
            self.vector_store.add_documents(texts, metadatas, ids)
    
    def _extract_structured_flags(self, filings_data: Dict) -> Dict[str, Any]:
        """Extract structured governance and event flags."""
        categorized = filings_data.get("categorized", {})
        shareholding = filings_data.get("shareholding") or {}
        
        flags = {
            "financial_results_count": len(categorized.get("financial_results", [])),
            "dividend_announced": len(categorized.get("dividend", [])) > 0,
            "buyback_announced": len([a for a in categorized.get("corporate_action", []) if "buyback" in a.get("subject", "").lower()]) > 0,
            "corporate_actions": [a.get("subject") for a in categorized.get("corporate_action", [])],
            "management_changes": [a.get("subject") for a in categorized.get("management_change", [])],
            "regulatory_actions": [a.get("subject") for a in categorized.get("regulatory", [])],
            "related_party_transactions": [a.get("subject") for a in categorized.get("related_party", [])],
            "promoter_holding_pct": shareholding.get("promoter_holding_pct"),
            "promoter_pledged_pct": shareholding.get("promoter_pledged_pct"),
            "fii_holding_pct": shareholding.get("fii_holding_pct"),
            "dii_holding_pct": shareholding.get("dii_holding_pct"),
        }
        
        # Governance red flags
        governance_flags = []
        if flags["promoter_pledged_pct"] and flags["promoter_pledged_pct"] > 20:
            governance_flags.append(f"High promoter pledge: {flags['promoter_pledged_pct']:.1f}%")
        if flags["regulatory_actions"]:
            governance_flags.append(f"Regulatory actions: {len(flags['regulatory_actions'])}")
        if flags["related_party_transactions"]:
            governance_flags.append(f"Related party transactions disclosed: {len(flags['related_party_transactions'])}")
        if flags["management_changes"]:
            governance_flags.append(f"Management changes: {len(flags['management_changes'])}")
            
        flags["governance_red_flags"] = governance_flags
        return flags
    
    def _run_llm_analysis(self, symbol: str, company_name: str, filings_data: Dict) -> Dict[str, Any]:
        """Run LLM qualitative filings analysis."""
        try:
            prompt = FILINGS_AGENT_PROMPT.format(
                symbol=symbol,
                company_name=company_name,
                announcements_json=json.dumps(filings_data.get("categorized", {}), indent=2, default=str),
                shareholding_json=json.dumps(filings_data.get("shareholding", {}), indent=2, default=str),
                presentations_json=json.dumps(filings_data.get("presentations", []), indent=2, default=str)
            )
            
            messages = [
                {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm.chat_structured(
                messages=messages,
                response_model=FilingsAnalysisOutput
            )
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM filings analysis failed for {symbol}: {e}")
            return {"error": str(e), "governance_concerns": ["Analysis unavailable"]}
    
    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "announcements_count": 0,
            "categorized": {},
            "shareholding": {},
            "presentations": [],
            "structured_flags": {},
            "qualitative_analysis": {"error": "No filings available"},
            "analyzed_at": date.today().isoformat()
        }