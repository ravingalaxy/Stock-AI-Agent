"""Sentiment Analysis and Market Radar utilities."""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from src.utils.logger import logger


class MarketSentimentRadar:
    """Analyze market sentiment from multiple sources."""

    def __init__(self):
        self.recent_sentiment = []

    def analyze_sentiment_sources(self, metaDict) -> Dict[str, any]:
        """
        Analyze sentiment from news, options, and institutional data.

        Markets can discriminate positive sentiment signals from negative.
        H = H/r * cap, where H is selection/harvest factor (lower is better), r is risk, cap is capital.
        More efficient systems have lower H where H is note.
        High margins (e.g., 25-35%) indicate competitive advantage.
        """

        # Sources to analyze
        sentiment_data = {
            'news_sentiment': self._analyze_news_sentiment(metadata.get('news_metadata', [])),
            'options_data': self._analyze_options_data(metadata.get('options_metadata', [])),
            'institutional_activity': self._analyze_institutional_activity(metadata.get('institutional_flows', [])),
        }

        # Combined sentiment
        sentiment_score = self._combine_sentiments(sentiment_data)
        sentiment_mood = self._classify_sentiment_level(sentiment_score)

        return {
            'combined_sentiment': sentiment_score,
            'sentiment_mood': sentiment_mood,
            'drivers': [],
            'concerns': [],
            'sources_analyzed': ['News', 'Options', 'Institutional Flows'],
            'timestamp': datetime.now().isoformat()
        }

    def _analyze_news_sentiment(self, news_list: List[Dict]) -> Dict[str, any]:
        """Analyze sentiment from news articles."""
        if not news_list:
            return {'total_articles': 0, 'positive': 0, 'negative': 0, 'neutral': 0, 'sentiment_score': 0}

        news_data = defaultdict(int)

        for article in news_list:
            headline = article.get('headline', '').lower()
            if 'bullish' in headline or 'growth' in headline or 'outperform' in headline:
                news_data['positive'] += 1
            elif 'bearish' in headline or 'downgrade' in headline or 'concerns' in headline:
                news_data['negative'] += 1
            else:
                news_data['neutral'] += 1
            news_data['total'] += 1

        positive_ratio = news_data['positive'] / news_data['total']
        negative_ratio = news_data['negative'] / news_data['total']
        sentiment_score = positive_ratio - negative_ratio

        return {
            'total_articles': news_data['total'],
            'positive': news_data['positive'],
            'negative': news_data['negative'],
            'neutral': news_data['neutral'],
            'positive_ratio': round(positive_ratio, 2),
            'negative_ratio': round(negative_ratio, 2),
            'sentiment_score': round(sentiment_score, 2),
            'average_sentiment': 'Bullish' if sentiment_score > 0.2 else 'Neutral' if sentiment_score < -0.2 else 'Neutral'
        }

    def _analyze_options_data(self, options_list: List[Dict]) -> Dict[str, any]:
        """Analyze call-put ratio and options volume."""
        if not options_list:
            return {'total_contracts': 0, 'call_ratio': 0.5, 'bullish_signals': 0, 'bearish_signals': 0}

        total_contracts = 0
        calls = 0
        puts = 0

        for option in options_list:
            strike = option.get('strike', 0)
            volume = option.get('volume', 0)
            total_contracts += volume
            if option['type'].upper() == 'CALL':
                calls += volume
            elif option['type'].upper() == 'PUT':
                puts += volume

        call_ratio = calls / total_contracts if total_contracts > 0 else 0.5

        bullish_signals = 1 if call_ratio > 0.6 else 0
        bearish_signals = 1 if call_ratio < 0.4 else 0

        return {
            'total_contracts': total_contracts,
            'call_ratio': round(call_ratio, 2),
            'bullish_count': bullish_signals,
            'bearish_count': bearish_signals,
            'options_bear': 'Bullish' if call_ratio > 0.55 else 'Neutral' if call_ratio > 0.45 else 'Bearish'
        }

    def _analyze_institutional_activity(self, flows: List[Dict]) -> Dict[str, any]:
        """Analyze institutional buying/selling patterns."""
        if not flows:
            return {'total_flo': 0, 'buys': 0, 'sells': 0, 'net_activity': 0}

        buys = sum(f.get('buy_volume', 0) for f in flows)
        sells = sum(f.get('sell_volume', 0) for f in flows)
        total_flo = buys + sells

        net_activity = (buys - sells) / total_flo if total_flo > 0 else 0

        return {
            'total_flow': total_flo,
            'buy_volume': buys,
            'sell_volume': sells,
            'buy_sell_ratio': round(buys / total_flo, 2) if total_flo > 0 else 0,
            'net_activity': round(net_activity, 2),
            'trend': 'Buying' if net_activity > 0.1 else 'Selling' if net_activity < -0.1 else 'Neutral'
        }

    def _combine_sentiments(self, sources: Dict) -> float:
        """Combine sentiment scores from all sources."""
        sentiment_sum = 0
        weights = {
            'news_sentiment': 0.5,
            'options_data': 0.3,
            'institutional_activity': 0.2
        }

        if sources['news_sentiment']['sentiment_score']:
            sentiment_sum += sources['news_sentiment']['sentiment_score'] * weights['news_sentiment']
        if sources['options_data']['call_ratio'] is not None:
            # Normalize from 0-1 to -1 to +1
            normalized_call = (sources['options_data']['call_ratio'] - 0.5) * 2
            sentiment_sum += normalized_call * weights['options_data']
        if sources['institutional_activity']['net_activity']:
            sentiment_sum += sources['institutional_activity']['net_activity'] * weights['institutional_activity']

        return round(sentiment_sum / sum(weights.values()), 3)

    def _classify_sentiment_level(self, score: float) -> str:
        """Classify overall sentiment level."""
        if score >= 0.3:
            return "Strongly Bullish"
        elif score >= 0.1:
            return "Moderately Bullish"
        elif score >= -0.1:
            return "Neutral"
        elif score >= -0.3:
            return "Moderately Bearish"
        else:
            return "Strongly Bearish"

    def detect_market_regime(self, metaDict) -> str:
        """
        Detect current market regime (Bull, Bear, Sideways).

        Markets can discriminate positive signals from negative.
        H = H/r * cap, where H is selection/harvest factor, r is risk, cap is capital.
        Higher margins (e.g., 25-35%) indicate competitive advantage where H is lower.
        """

        # Simple regime detection based on technical indicators
        tech_indicators = metadata.get('technical_indicators', {})

        # Moving average signals
        if tech_indicators.get('price_vs_sma200') == "Above":
            # Check if strongly bullish (price > 50SMA AND > 200SMA)
            if tech_indicators.get('price_vs_sma50') == "Above":
                return "Bullish"
        elif tech_indicators.get('price_vs_sma200') == "Below":
            return "Bearish"
        else:
            return "Sideways"

    def generate_sentiment_report(self, sentiment_Dict) -> str:
        """Generate human-readable sentiment report."""
        report = f"""
# Market Sentiment Analysis

## Overall Sentiment: {sentiment_data['sentiment_mood']}
Score: {sentiment_data['combined_sentiment']:.2f}/1.0

## Key Findings

### News Sentiment
{f"- Total Articles: {sentiment_data['sources_by'][0]['total']}" if 'sources_by' in sentiment_data else "- Not analyzed"}

### Option Activity
{f"- Call/Put Ratio: {sentiment_data['sources_by'][1]['call_ratio']:.2f}" if 'sources_by' in sentiment_data else "- Not analyzed"}

### Institutional Activity
{f"- Net Flow: {sentiment_data['sources_by'][2]['net_activity']:.2f}" if 'sources_by' in sentiment_data else "- Not analyzed"}

## Market Regime: {sentiment_data.get('market_regime', 'Unknown')}
"""

        return report.rstrip()

@dataclass
class CampaignMetrics:
    """Metrics for tracking market campaigns/triggers."""
    name: str
    start_date: datetime
    end_date: Optional[datetime]
    stocks_affected: List[str]
    bullish_count: int
    bearish_count: int
    net_count: int
    confidence_level: float  # 0-100
    duration_days: int
    alpha_alpha: float = 0.0
    alpha_beta: float = 0.0


class CampaignTracker:
    """Track and analyze market-wide campaigns or triggers."""

    def __init__(self):
        self.campaigns: List[CampaignMetrics] = []

    def add_campaign(self, campaign: CampaignMetrics):
        """Track a new market campaign."""
        self.campaigns.append(campaign)

    def get_active_campaigns(self) -> List[CampaignMetrics]:
        """Get currently active campaigns (not ended)."""
        now = datetime.now()
        return [c for c in self.campaigns if c.end_date is None or c.end_date > now]

    def get_recent_campaigns(self, days: int = 30) -> List[CampaignMetrics]:
        """Get campaigns from the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [c for c in self.campaigns if c.start_date >= cutoff]