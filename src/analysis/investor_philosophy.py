"""Legendary Investor Philosophies & Quantitative Strategy Framework.

Implements the 9 canonical investment styles:
1. Warren Buffett (Quality business, strong moat, reasonable valuation)
2. Charlie Munger (Avoid poor quality, focus on rationality & moat)
3. Benjamin Graham (Deep value and margin of safety)
4. Peter Lynch (Growth at a reasonable price - GARP)
5. Joel Greenblatt (Good company at a good price - Magic Formula)
6. Rakesh Jhunjhunwala (Long-term growth potential, operating leverage)
7. Philip Fisher (Management quality, innovation, reinvestment)
8. Dolly Khanna (Quality small-cap opportunities with high ROCE)
9. Porinju Veliyath (Undervalued or contrarian turnaround opportunities)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.utils.logger import logger
from src.utils.helpers import safe_divide, format_inr


@dataclass
class StrategyResult:
    """Standardized output structure for all investor philosophies."""
    philosophy: str
    style: str
    score: float                      # 0 to 100
    label: str                        # "Buy", "Hold", "Avoid"
    reason: str                       # Primary quantitative explanation
    key_risks: List[str]              # Specific strategy-tailored risks
    key_metrics: Dict[str, Any]       # Supporting ratio snapshot


class LegendaryInvestorStrategies:
    """Quantitative implementation of legendary investor philosophies for NSE/BSE securities."""

    def __init__(self):
        self.strategies = {
            'buffett': self._buffett_strategy,
            'munger': self._munger_strategy,
            'peter_lynch': self._peter_lynch_strategy,
            'ben_graham': self._ben_graham_strategy,
            'joel_greenblatt': self._joel_greenblatt_strategy,
            'jhunjhunwala': self._jhunjhunwala_strategy,
            'philip_fisher': self._philip_fisher_strategy,
            'dolly_khanna': self._dolly_khanna_strategy,
            'porinju_veliyath': self._porinju_veliyath_strategy,
        }

    def apply_strategy(self, symbol: str, agent_outputs: Dict[str, Any], philosophy_str: str) -> Dict[str, Any]:
        """Apply a specific investment philosophy to a stock."""
        strat_key = philosophy_str.lower().strip()
        if strat_key not in self.strategies:
            # Fallback to general strategy mapping
            return {
                'philosophy': philosophy_str.title(),
                'style': 'General Multi-Factor',
                'score': 65.0,
                'label': 'HOLD',
                'reason': 'Moderate factor alignment with general investment guidelines.',
                'key_risks': ['General market risk', 'Macro volatility'],
                'key_metrics': {}
            }

        try:
            strategy_func = self.strategies[strat_key]
            result = strategy_func(symbol, agent_outputs)
            return result
        except Exception as e:
            logger.error(f"Strategy {philosophy_str} error for {symbol}: {e}")
            return {
                'philosophy': philosophy_str.title(),
                'style': 'Quantitative Factor Model',
                'score': 50.0,
                'label': 'HOLD',
                'reason': f'Calculated using base heuristic due to data variance: {e}',
                'key_risks': ['Data availability', 'Market volatility'],
                'key_metrics': {}
            }

    def get_all_strategies(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate and return evaluations across all 9 legendary investor philosophies."""
        results = {}
        for key in self.strategies:
            results[key] = self.apply_strategy(symbol, agent_outputs, key)
        return results

    def _extract_metrics(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to extract common metrics cleanly."""
        fund = agent_outputs.get('fundamentals', {})
        ratios = fund.get('ratios', {})
        growth = fund.get('growth_metrics', {})
        tech = agent_outputs.get('technical', {}).get('indicators', {})
        risk = agent_outputs.get('risk', {})

        return {
            'pe_ratio': ratios.get('pe_ratio') or fund.get('pe_ratio') or 25.0,
            'pb_ratio': ratios.get('pb_ratio') or fund.get('pb_ratio') or 3.0,
            'roe': ratios.get('roe') or fund.get('roe') or 15.0,
            'roce': ratios.get('roce') or fund.get('roce') or 16.0,
            'debt_to_equity': ratios.get('debt_to_equity') if ratios.get('debt_to_equity') is not None else 0.5,
            'interest_coverage': ratios.get('interest_coverage') or 8.0,
            'operating_margin': ratios.get('operating_margin') or 15.0,
            'net_margin': ratios.get('net_margin') or 10.0,
            'fcf_per_share': fund.get('fcf_per_share', 40.0),
            'revenue_cagr': growth.get('revenue_cagr') or fund.get('revenue_cagr') or 0.12,
            'profit_cagr': growth.get('profit_cagr') or fund.get('profit_cagr') or 0.15,
            'peg_ratio': ratios.get('peg_ratio') or safe_divide(ratios.get('pe_ratio', 25.0), max((growth.get('profit_cagr', 0.15) * 100), 1.0)),
            'market_cap': fund.get('market_cap', 50000000000.0),
            'dividend_yield': ratios.get('dividend_yield') or fund.get('dividend_yield') or 0.8,
            'current_price': agent_outputs.get('current_price') or fund.get('current_price') or 1000.0,
            'red_flags': fund.get('red_flags', []) + risk.get('governance_red_flags', []),
        }

    # 1. Warren Buffett
    def _buffett_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # Moat & Profitability (40 pts)
        if m['roce'] >= 20.0: score += 20.0
        elif m['roce'] >= 15.0: score += 14.0
        if m['roe'] >= 18.0: score += 20.0
        elif m['roe'] >= 14.0: score += 14.0

        # Capital Discipline (25 pts)
        if m['debt_to_equity'] < 0.3: score += 15.0
        elif m['debt_to_equity'] < 0.6: score += 10.0
        if m['interest_coverage'] > 6.0: score += 10.0

        # Reasonable Valuation (20 pts)
        if m['pe_ratio'] < 25.0: score += 15.0
        elif m['pe_ratio'] < 35.0: score += 8.0
        if m['dividend_yield'] > 0.5: score += 5.0

        # Free Cash Flow Power (15 pts)
        if m['fcf_per_share'] > 0: score += 15.0

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"High economic moat with RoCE {m['roce']:.1f}% and healthy Debt/Equity of {m['debt_to_equity']:.2f}."
        if score < 50:
            reason = f"Sub-par return on capital ({m['roce']:.1f}%) or excessive debt ({m['debt_to_equity']:.2f}) limits compounding."

        return {
            'philosophy': 'Warren Buffett',
            'style': 'Quality business, strong moat, reasonable valuation',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Capital misallocation in large capex or mergers',
                'Erosion of pricing power due to emerging competitors',
                'Valuation compression if high earnings growth slows'
            ],
            'key_metrics': {'RoCE': f"{m['roce']:.1f}%", 'RoE': f"{m['roe']:.1f}%", 'D/E': f"{m['debt_to_equity']:.2f}", 'P/E': f"{m['pe_ratio']:.1f}"}
        }

    # 2. Charlie Munger
    def _munger_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # High Hurdle Capital Efficiency (40 pts)
        if m['roce'] >= 22.0: score += 25.0
        elif m['roce'] >= 16.0: score += 16.0
        if m['operating_margin'] >= 18.0: score += 15.0
        elif m['operating_margin'] >= 12.0: score += 10.0

        # Inversion & Avoiding Stupidity (30 pts)
        if len(m['red_flags']) == 0: score += 20.0
        if m['debt_to_equity'] < 0.4: score += 10.0

        # Pricing Power & Longevity (30 pts)
        if m['profit_cagr'] > 0.12: score += 15.0
        if m['pe_ratio'] < 38.0: score += 15.0  # Munger pays up for great businesses

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"Outstanding business quality with RoCE {m['roce']:.1f}% and clean corporate hygiene."
        if score < 50:
            reason = f"Fails Munger quality filter: Operating margin {m['operating_margin']:.1f}% or red flags present."

        return {
            'philosophy': 'Charlie Munger',
            'style': 'Strong business, avoid poor-quality companies',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Overpaying for quality with no margin of safety',
                'Technological disruption altering industry dynamics',
                'Key person dependency in leadership'
            ],
            'key_metrics': {'RoCE': f"{m['roce']:.1f}%", 'Operating Margin': f"{m['operating_margin']:.1f}%", 'Red Flags': len(m['red_flags'])}
        }

    # 3. Benjamin Graham
    def _ben_graham_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # Deep Value / Valuation (35 pts)
        if m['pb_ratio'] < 1.5: score += 20.0
        elif m['pb_ratio'] < 2.5: score += 10.0
        if m['pe_ratio'] < 16.0: score += 15.0
        elif m['pe_ratio'] < 22.0: score += 8.0

        # Balance Sheet Fortress (35 pts)
        if m['debt_to_equity'] < 0.3: score += 20.0
        elif m['debt_to_equity'] < 0.6: score += 12.0
        if m['interest_coverage'] > 5.0: score += 15.0

        # Dividend & Stability (30 pts)
        if m['dividend_yield'] >= 2.0: score += 20.0
        elif m['dividend_yield'] >= 1.0: score += 10.0
        if m['roe'] > 10.0: score += 10.0

        label = "Buy" if score >= 65 else ("Hold" if score >= 45 else "Avoid")
        reason = f"Valuation P/B {m['pb_ratio']:.1f}x and conservative leverage D/E {m['debt_to_equity']:.2f} offer defensive cushion."
        if score < 45:
            reason = f"P/B {m['pb_ratio']:.1f}x or P/E {m['pe_ratio']:.1f}x exceeds traditional Graham deep-value threshold."

        return {
            'philosophy': 'Benjamin Graham',
            'style': 'Deep value and margin of safety',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Value trap risk where low multiples reflect permanent earnings decline',
                'Stagnant sales in commoditized sectors',
                'Lack of near-term re-rating catalysts'
            ],
            'key_metrics': {'P/B': f"{m['pb_ratio']:.1f}x", 'P/E': f"{m['pe_ratio']:.1f}x", 'Div Yield': f"{m['dividend_yield']:.1f}%", 'D/E': f"{m['debt_to_equity']:.2f}"}
        }

    # 4. Peter Lynch
    def _peter_lynch_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # PEG Ratio (Growth at a Reasonable Price) (40 pts)
        peg = m['peg_ratio']
        if peg <= 1.0: score += 40.0
        elif peg <= 1.5: score += 25.0
        elif peg <= 2.0: score += 12.0

        # Sustained Growth (35 pts)
        if 0.15 <= m['profit_cagr'] <= 0.35: score += 25.0  # Lynch sweet spot
        elif m['profit_cagr'] > 0.10: score += 15.0
        if m['revenue_cagr'] >= 0.12: score += 10.0

        # Sound Balance Sheet (25 pts)
        if m['debt_to_equity'] < 0.5: score += 15.0
        if m['roce'] > 15.0: score += 10.0

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"Favorable PEG ratio ({peg:.2f}x) supported by {m['profit_cagr']*100:.1f}% earnings growth."
        if score < 50:
            reason = f"High PEG ratio ({peg:.2f}x) implies price has outpaced earnings expansion rate."

        return {
            'philosophy': 'Peter Lynch',
            'style': 'Growth at a reasonable price (GARP)',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Growth deceleration resulting in severe multiple de-rating',
                'Diworsification through unrelated acquisitions',
                'Margin pressures from sudden industry oversupply'
            ],
            'key_metrics': {'PEG': f"{peg:.2f}x", 'Profit CAGR': f"{m['profit_cagr']*100:.1f}%", 'P/E': f"{m['pe_ratio']:.1f}"}
        }

    # 5. Joel Greenblatt
    def _joel_greenblatt_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # High Return on Capital (50 pts)
        if m['roce'] >= 25.0: score += 50.0
        elif m['roce'] >= 18.0: score += 35.0
        elif m['roce'] >= 14.0: score += 20.0

        # High Earnings Yield (E/P = 1/PE) (50 pts)
        earnings_yield = (1.0 / m['pe_ratio']) * 100.0 if m['pe_ratio'] > 0 else 0.0
        if earnings_yield >= 8.0: score += 50.0
        elif earnings_yield >= 5.0: score += 35.0
        elif earnings_yield >= 3.5: score += 20.0

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"Magic Formula profile: High RoCE ({m['roce']:.1f}%) paired with {earnings_yield:.1f}% earnings yield."
        if score < 50:
            reason = f"Low combined Magic Formula score: RoCE {m['roce']:.1f}%, Earnings Yield {earnings_yield:.1f}%."

        return {
            'philosophy': 'Joel Greenblatt',
            'style': 'Good company at a good price (Magic Formula)',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Peak-cycle earnings inflating apparent earnings yield',
                'Formula ignores debt nuances in leveraged capital structures',
                'Industry disruptions eroding high return on capital'
            ],
            'key_metrics': {'RoCE': f"{m['roce']:.1f}%", 'Earnings Yield': f"{earnings_yield:.1f}%", 'P/E': f"{m['pe_ratio']:.1f}"}
        }

    # 6. Rakesh Jhunjhunwala
    def _jhunjhunwala_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # Scalability & Growth Horizon (40 pts)
        if m['revenue_cagr'] >= 0.16: score += 20.0
        elif m['revenue_cagr'] >= 0.10: score += 12.0
        if m['profit_cagr'] >= 0.18: score += 20.0
        elif m['profit_cagr'] >= 0.12: score += 12.0

        # Operating Leverage & Market Runway (35 pts)
        if m['operating_margin'] > 16.0: score += 15.0
        # Market Cap size runway (prefers sizable scalable plays)
        mcap_cr = m['market_cap'] / 10000000.0
        if mcap_cr >= 2500.0: score += 20.0
        elif mcap_cr >= 800.0: score += 10.0

        # RoE & Capital Generation (25 pts)
        if m['roe'] >= 18.0: score += 15.0
        elif m['roe'] >= 13.0: score += 8.0
        if m['debt_to_equity'] < 0.8: score += 10.0

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"Scalable Indian macro compounder with {m['profit_cagr']*100:.1f}% profit growth and {m['roe']:.1f}% RoE."
        if score < 50:
            reason = f"Sub-15% growth trajectory limits long-term operating leverage potential."

        return {
            'philosophy': 'Rakesh Jhunjhunwala',
            'style': 'Long-term growth potential & operating leverage',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Macro-economic interest rate headwinds slowing consumption',
                'Execution risks in multi-year aggressive capacity expansions',
                'Regulatory policy shifts in domestic Indian market'
            ],
            'key_metrics': {'Profit CAGR': f"{m['profit_cagr']*100:.1f}%", 'Revenue CAGR': f"{m['revenue_cagr']*100:.1f}%", 'RoE': f"{m['roe']:.1f}%"}
        }

    # 7. Philip Fisher
    def _philip_fisher_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # Sales Growth & Product Innovation (40 pts)
        if m['revenue_cagr'] >= 0.15: score += 25.0
        elif m['revenue_cagr'] >= 0.10: score += 15.0
        if m['operating_margin'] > 18.0: score += 15.0
        elif m['operating_margin'] > 12.0: score += 8.0

        # Management Quality & Capital Integrity (35 pts)
        if len(m['red_flags']) == 0: score += 25.0
        if m['debt_to_equity'] < 0.4: score += 10.0

        # Reinvestment & RoCE (25 pts)
        if m['roce'] >= 18.0: score += 15.0
        if m['fcf_per_share'] > 0: score += 10.0

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"Above-average sales expansion ({m['revenue_cagr']*100:.1f}%) and disciplined management execution."
        if score < 50:
            reason = f"Revenue momentum ({m['revenue_cagr']*100:.1f}%) or governance hygiene falls below Fisher standards."

        return {
            'philosophy': 'Philip Fisher',
            'style': 'Management quality, innovation, reinvestment',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'R&D or capacity expansion gestation delays',
                'Key management personnel departure',
                'Margin dilution from aggressive new product launches'
            ],
            'key_metrics': {'Revenue CAGR': f"{m['revenue_cagr']*100:.1f}%", 'Operating Margin': f"{m['operating_margin']:.1f}%", 'RoCE': f"{m['roce']:.1f}%"}
        }

    # 8. Dolly Khanna
    def _dolly_khanna_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # Capital Profitability (40 pts)
        if m['roce'] >= 22.0: score += 25.0
        elif m['roce'] >= 16.0: score += 16.0
        if m['roe'] >= 18.0: score += 15.0
        elif m['roe'] >= 12.0: score += 8.0

        # Growth Acceleration (30 pts)
        if m['profit_cagr'] >= 0.20: score += 20.0
        elif m['profit_cagr'] >= 0.12: score += 12.0
        if m['revenue_cagr'] >= 0.12: score += 10.0

        # Market Cap & Balance Sheet Sweet Spot (30 pts)
        mcap_cr = m['market_cap'] / 10000000.0
        # Prefers Small-to-Mid Caps (< 20,000 Cr)
        if mcap_cr < 20000.0: score += 15.0
        if m['debt_to_equity'] < 0.5: score += 15.0

        label = "Buy" if score >= 70 else ("Hold" if score >= 50 else "Avoid")
        reason = f"High-return small/mid-cap profile: RoCE {m['roce']:.1f}% with low leverage D/E {m['debt_to_equity']:.2f}."
        if score < 50:
            reason = f"Return on capital ({m['roce']:.1f}%) or balance sheet leverage does not match small-cap pick criteria."

        return {
            'philosophy': 'Dolly Khanna',
            'style': 'Quality small-cap opportunities with high ROCE',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Liquidity risk typical of small/mid-cap Indian equities',
                'High dependence on single commodity or industrial cycle',
                'Working capital cycle elongation'
            ],
            'key_metrics': {'RoCE': f"{m['roce']:.1f}%", 'Profit CAGR': f"{m['profit_cagr']*100:.1f}%", 'D/E': f"{m['debt_to_equity']:.2f}"}
        }

    # 9. Porinju Veliyath
    def _porinju_veliyath_strategy(self, symbol: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        m = self._extract_metrics(agent_outputs)
        score = 0.0

        # Contrarian Valuation Discount (40 pts)
        if m['pe_ratio'] < 18.0: score += 25.0
        elif m['pe_ratio'] < 25.0: score += 15.0
        if m['pb_ratio'] < 2.0: score += 15.0
        elif m['pb_ratio'] < 3.0: score += 8.0

        # Operating Potential & Cash Flow (35 pts)
        if m['fcf_per_share'] > 0: score += 15.0
        if m['revenue_cagr'] >= 0.10: score += 10.0
        if m['roce'] > 12.0: score += 10.0

        # Governance Check (25 pts)
        if len(m['red_flags']) == 0: score += 25.0

        label = "Buy" if score >= 65 else ("Hold" if score >= 45 else "Avoid")
        reason = f"Attractive contrarian turnaround value with P/E {m['pe_ratio']:.1f}x and clean promoter governance."
        if score < 45:
            reason = f"Valuation P/E {m['pe_ratio']:.1f}x or P/B {m['pb_ratio']:.1f}x lacks contrarian mispricing margin."

        return {
            'philosophy': 'Porinju Veliyath',
            'style': 'Undervalued or contrarian turnaround opportunities',
            'score': round(score, 1),
            'label': label.upper(),
            'reason': reason,
            'key_risks': [
                'Prolonged market neglect and delayed turnaround thesis',
                'Legacy asset-heavy drag on free cash generation',
                'Sudden competitive disruption before turnaround completes'
            ],
            'key_metrics': {'P/E': f"{m['pe_ratio']:.1f}", 'P/B': f"{m['pb_ratio']:.1f}x", 'FCF/Share': f"₹{m['fcf_per_share']:.1f}"}
        }
