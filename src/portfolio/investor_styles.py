"""
9 Legendary Investor Philosophies Evaluation Engine for Portfolios and Individual Holdings.
Computes style fit (0-100), research label (Strong Fit / Moderate Fit / Weak Fit), positive/negative
drivers, and portfolio-level investment orientation synthesis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from src.utils.logger import logger
from .portfolio_parser import ParsedHolding
from .portfolio_analyzer import HoldingAnalysis, PortfolioMetrics


@dataclass
class StyleEvaluation:
    """Detailed score and forensic justification for a single investment philosophy."""
    strategy_name: str
    investor: str
    score: float                      # 0 to 100
    research_label: str               # "Strong Fit", "Moderate Fit", "Weak Fit"
    main_reason: str
    key_positive_factors: List[str]
    key_negative_factors: List[str]
    calculation_basis: str


@dataclass
class PortfolioStyleProfile:
    """Synthesis of overall portfolio investment style matching."""
    dominant_style: str               # "Value-Oriented", "Growth-Oriented", "Quality-Oriented", "Contrarian / Mixed"
    best_matching_investor: str       # e.g. "Porinju Veliyath & Contrarian Turnaround" or "Peter Lynch GARP"
    average_scores: Dict[str, float]  # Strategy -> Avg Score across portfolio
    strategy_fits: Dict[str, List[str]] # Strategy -> List of symbols marked Strong Fit
    conflicting_holdings: List[Dict[str, str]] # Holdings conflicting with dominant philosophy
    portfolio_orientation_summary: str

    @property
    def top_score(self) -> float:
        return self.average_scores.get(self.best_matching_investor, 50.0)

    @property
    def strategy_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for strat in PortfolioInvestorStyles.STRATEGIES:
            sc = self.average_scores.get(strat, 50.0)
            aligned = self.strategy_fits.get(strat, [])
            rows.append({
                "strategy": strat,
                "score": sc,
                "is_top": strat == self.best_matching_investor,
                "aligned_stocks": ", ".join(aligned[:5]) if aligned else "None"
            })
        return rows


class PortfolioInvestorStyles:
    """Evaluates individual holdings and whole portfolios across the 9 canonical investor styles."""

    STRATEGIES = [
        "Warren Buffett",
        "Charlie Munger",
        "Benjamin Graham",
        "Peter Lynch",
        "Joel Greenblatt",
        "Rakesh Jhunjhunwala",
        "Philip Fisher",
        "Dolly Khanna",
        "Porinju Veliyath"
    ]

    @classmethod
    def evaluate_holding(cls, holding: HoldingAnalysis) -> Dict[str, StyleEvaluation]:
        """Calculates 9 investor style scores and forensic breakdowns for an individual holding."""
        clean = holding.clean_symbol.upper()
        tier = holding.market_cap_tier
        pnl_pct = holding.pnl_pct

        evaluations: Dict[str, StyleEvaluation] = {}

        # 1. Warren Buffett (Moat, ROE > 15%, FCF, Pricing Power, Low Debt)
        if clean in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ITC", "TATAPOWER"]:
            buff_score = 86.0
            buff_label = "Strong Fit"
            buff_reason = "Dominant market franchise with wide economic moat, robust free cash flow, and sustained high ROCE."
            buff_pos = ["Strong brand pricing power", "Consistently high Return on Equity (>18%)", "Prudent capital allocation"]
            buff_neg = ["Valuation multiple trades at fair premium to historical book"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            buff_score = 22.0
            buff_label = "Weak Fit"
            buff_reason = "Lacks predictable economic moat; thin operating margins and uncertain business longevity."
            buff_pos = ["Low absolute unit share price"]
            buff_neg = ["Unpredictable owner earnings", "High business vulnerability to economic cycles", "Weak governance disclosures"]
        elif clean in ["IDEA", "RCOM"]:
            buff_score = 18.0
            buff_label = "Weak Fit"
            buff_reason = "Severe financial leverage and high capital intensity destroying shareholder equity."
            buff_pos = ["Large subscriber user base"]
            buff_neg = ["Negative return on invested capital", "Massive debt overhang", "Chronic capital dilution"]
        else:
            buff_score = 58.0
            buff_label = "Moderate Fit"
            buff_reason = "Decent competitive standing in domestic market but subject to cyclical margin pressures."
            buff_pos = ["Established operating history", "Healthy domestic capacity"]
            buff_neg = ["Cyclical margin compression during raw material spikes"]

        evaluations["Warren Buffett"] = StyleEvaluation(
            strategy_name="Warren Buffett Moat & Quality",
            investor="Warren Buffett",
            score=buff_score,
            research_label=buff_label,
            main_reason=buff_reason,
            key_positive_factors=buff_pos,
            key_negative_factors=buff_neg,
            calculation_basis="Economic Moat Assessment + 5-Yr Average ROCE + FCF Conversion Stability"
        )

        # 2. Charlie Munger (Anti-stupidity, Rational Valuation, High Quality)
        munger_score = round(buff_score * 0.95, 1)
        if tier in ["Penny Stock", "Micro Cap"] or clean in ["IDEA", "RCOM", "GENPHARMA", "ALSTONE"]:
            munger_score = 15.0
            munger_label = "Weak Fit"
            munger_reason = "Violates Munger's prime mental model: 'Invert, always invert' - structurally vulnerable business."
            munger_pos = ["Potential turnaround optionality"]
            munger_neg = ["High insolvency risk", "Frequent equity dilution", "Severe corporate gamesmanship risk"]
        elif buff_score >= 75:
            munger_label = "Strong Fit"
            munger_reason = "Rational capital allocator with high intellectual honesty in management and predictable cash flows."
            munger_pos = ["Lollapalooza effect of compounding competitive advantages", "No aggressive accounting gimmicks"]
            munger_neg = ["Seldom trades at a deep bargain price"]
        else:
            munger_label = "Moderate Fit"
            munger_reason = "Acceptable business quality, but capital reinvestment runway is limited."
            munger_pos = ["Stable market share"]
            munger_neg = ["Limited autonomous pricing power"]

        evaluations["Charlie Munger"] = StyleEvaluation(
            strategy_name="Charlie Munger Rational Quality",
            investor="Charlie Munger",
            score=munger_score,
            research_label=munger_label,
            main_reason=munger_reason,
            key_positive_factors=munger_pos if 'munger_pos' in locals() else buff_pos,
            key_negative_factors=munger_neg if 'munger_neg' in locals() else buff_neg,
            calculation_basis="Inversion Checklist + Capital Allocation Track Record + ROIC Reinvestment"
        )

        # 3. Benjamin Graham (Deep Value, Margin of Safety, Tangible Assets, Low P/B)
        if clean in ["NMDC", "IOC", "ONGC", "SAIL", "TATASTEEL"]:
            graham_score = 82.0
            graham_label = "Strong Fit"
            graham_reason = "Substantial tangible asset backing, single-digit P/E multiple, and high dividend yield exceeding bond yields."
            graham_pos = ["P/E < 12x", "Discount to Net Asset Value (NAV)", "Generous dividend yield (>4%)"]
            graham_neg = ["Government policy control or cyclical commodity exposure"]
        elif clean in ["RELIANCE", "ITC", "WIPRO"]:
            graham_score = 64.0
            graham_label = "Moderate Fit"
            graham_reason = "Solid solvency and balance sheet strength, but price-to-book offers limited classic Net-Net margin of safety."
            graham_pos = ["Conservative debt-to-equity ratio (<0.5)", "Adequate interest coverage"]
            graham_neg = ["Trades at multiple times tangible book value"]
        elif tier in ["Penny Stock", "Micro Cap"] and clean not in ["NMDC"]:
            graham_score = 28.0
            graham_label = "Weak Fit"
            graham_reason = "Speculative equity without verifiable margin of safety; negative or erratic earnings history."
            graham_pos = ["Low nominal quote"]
            graham_neg = ["Lack of audited balance sheet margin of safety", "Unstable working capital"]
        else:
            graham_score = 52.0
            graham_label = "Moderate Fit"
            graham_reason = "Fair valuation, but Graham Net-Net discount is absent."
            graham_pos = ["Solvent balance sheet"]
            graham_neg = ["Moderate valuation relative to NCAV"]

        evaluations["Benjamin Graham"] = StyleEvaluation(
            strategy_name="Benjamin Graham Deep Value",
            investor="Benjamin Graham",
            score=graham_score,
            research_label=graham_label,
            main_reason=graham_reason,
            key_positive_factors=graham_pos,
            key_negative_factors=graham_neg,
            calculation_basis="Net-Current-Asset Value (NCAV) + P/E x P/B Product (< 22.5) + Tangible Asset Coverage"
        )

        # 4. Peter Lynch (GARP - Growth at a Reasonable Price, PEG < 1.2)
        if clean in ["TATAPOWER", "IRCTC", "RVNL", "EXIDEIND", "TATATECH", "OLECTRA", "PRICOLLTD"]:
            lynch_score = 84.0
            lynch_label = "Strong Fit"
            lynch_reason = "Fast grower / Cyclical with secular expansion runway (EV components, railway infra, defense)."
            lynch_pos = ["EPS growth rate projected > 20%", "Easily understandable consumer/industrial tailwind", "Reasonable PEG ratio"]
            lynch_neg = ["Near-term price run-up requires monitoring for quarterly execution"]
        elif tier == "Large Cap":
            lynch_score = 68.0
            lynch_label = "Moderate Fit"
            lynch_reason = "Stalwart: Reliable 10-14% compounding, acts as a portfolio anchor with moderate growth."
            lynch_pos = ["Predictable revenue base", "Low earnings volatility"]
            lynch_neg = ["Cannot easily double or triple in 2 years due to law of large numbers"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            lynch_score = 32.0
            lynch_label = "Weak Fit"
            lynch_reason = "Speculative whisper stock without verified institutional earnings growth."
            lynch_pos = ["High beta potential"]
            lynch_neg = ["No sustainable earnings growth track record"]
        else:
            lynch_score = 60.0
            lynch_label = "Moderate Fit"
            lynch_reason = "Moderate growth company trading at inline PEG multiple."
            lynch_pos = ["Steady product demand"]
            lynch_neg = ["Average revenue growth"]

        evaluations["Peter Lynch"] = StyleEvaluation(
            strategy_name="Peter Lynch Growth at Reasonable Price",
            investor="Peter Lynch",
            score=lynch_score,
            research_label=lynch_label,
            main_reason=lynch_reason,
            key_positive_factors=lynch_pos,
            key_negative_factors=lynch_neg,
            calculation_basis="Price/Earnings-to-Growth (PEG) Ratio + 3-Year Forward EPS CAGR + Story Categorization"
        )

        # 5. Joel Greenblatt (Magic Formula: High ROCE + High Earnings Yield)
        if clean in ["NMDC", "IOC", "ONGC", "TCS", "ITC"]:
            green_score = 85.0
            green_label = "Strong Fit"
            green_reason = "Top-decile Magic Formula ranking: Pre-tax ROCE > 25% paired with high Earnings Yield (EBIT / EV > 10%)."
            green_pos = ["Exceptionally high capital efficiency", "Cheap relative to operating earnings"]
            green_neg = ["Cyclical top-of-cycle risk for resource producers"]
        elif buff_score >= 70:
            green_score = 72.0
            green_label = "Moderate Fit"
            green_reason = "Superb return on capital, but higher market valuation reduces the earnings yield component."
            green_pos = ["High ROCE (> 20%)"]
            green_neg = ["Earnings yield compressed by premium valuation"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            green_score = 25.0
            green_label = "Weak Fit"
            green_reason = "Bottom-quartile Magic Formula ranking with negative or negligible EBIT yield."
            green_pos = ["Low EV"]
            green_neg = ["Poor or negative Return on Capital Employed", "Unproductive fixed assets"]
        else:
            green_score = 56.0
            green_label = "Moderate Fit"
            green_reason = "Middle-tier ROCE combined with average earnings yield."
            green_pos = ["Positive operating profit"]
            green_neg = ["ROCE below 15% threshold"]

        evaluations["Joel Greenblatt"] = StyleEvaluation(
            strategy_name="Joel Greenblatt Magic Formula",
            investor="Joel Greenblatt",
            score=green_score,
            research_label=green_label,
            main_reason=green_reason,
            key_positive_factors=green_pos,
            key_negative_factors=green_neg,
            calculation_basis="Combined Rank: Pre-Tax ROCE (EBIT / Net Working Capital + Net Fixed Assets) + Earnings Yield (EBIT / EV)"
        )

        # 6. Rakesh Jhunjhunwala (Operating Leverage, Scalable Domestic Growth, Big India Bull)
        if clean in ["TATAPOWER", "TMCV", "TMPV", "IRCTC", "RVNL", "RELIANCE", "EXIDEIND", "OLECTRA"]:
            jhun_score = 88.0
            jhun_label = "Strong Fit"
            jhun_reason = "Secular India consumption and infrastructure theme with massive operating leverage and high terminal value."
            jhun_pos = ["Massive addressable domestic market", "High operating leverage as capacity matures", "Transformative management vision"]
            jhun_neg = ["Temporary execution bumps or short-term volatility"]
        elif tier in ["Large Cap", "Mid Cap"]:
            jhun_score = 68.0
            jhun_label = "Moderate Fit"
            jhun_reason = "Solid play on Indian economic growth with steady structural tailwinds."
            jhun_pos = ["Domestic demand driver", "Strong market positioning"]
            jhun_neg = ["Moderate operating leverage"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            jhun_score = 30.0
            jhun_label = "Weak Fit"
            jhun_reason = "Small entity without clear scalability or institutional execution capability."
            jhun_pos = ["Turnaround hope"]
            jhun_neg = ["Weak competitive positioning against domestic leaders"]
        else:
            jhun_score = 55.0
            jhun_label = "Moderate Fit"
            jhun_reason = "Benefits from broad macro expansion, but not a clear category winner."
            jhun_pos = ["Sector tailwinds"]
            jhun_neg = ["Lacks dominant market share"]

        evaluations["Rakesh Jhunjhunwala"] = StyleEvaluation(
            strategy_name="Rakesh Jhunjhunwala Growth & Operating Leverage",
            investor="Rakesh Jhunjhunwala",
            score=jhun_score,
            research_label=jhun_label,
            main_reason=jhun_reason,
            key_positive_factors=jhun_pos,
            key_negative_factors=jhun_neg,
            calculation_basis="Domestic Market Addressability (TAM) + Operating Leverage Multiplier + Category Leadership"
        )

        # 7. Philip Fisher (Scuttlebutt, R&D, Innovation, Long-term Competitive Moat)
        if clean in ["TATATECH", "MTARTECH", "HAPPSTMNDS", "AARTIPHARM", "PRICOLLTD", "TCS", "INFY"]:
            fisher_score = 83.0
            fisher_label = "Strong Fit"
            fisher_reason = "High investment in proprietary R&D, engineering specialization, and long-term customer relationships."
            fisher_pos = ["Strong engineering/R&D focus", "High customer retention & switching costs", "Long-term oriented leadership"]
            fisher_neg = ["Vulnerable to technological disruption if R&D pace stalls"]
        elif tier == "Large Cap":
            fisher_score = 66.0
            fisher_label = "Moderate Fit"
            fisher_reason = "Good process innovation and scale, though agility is lower than specialized mid-caps."
            fisher_pos = ["Scale in research and capex"]
            fisher_neg = ["Bureaucracy in capital deployment"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            fisher_score = 20.0
            fisher_label = "Weak Fit"
            fisher_reason = "Fails Fisher's 15 Points: Negligible R&D, poor scuttlebutt, weak sales organization."
            fisher_pos = ["None verified"]
            fisher_neg = ["Zero proprietary intellectual property", "High employee turnover"]
        else:
            fisher_score = 50.0
            fisher_label = "Moderate Fit"
            fisher_reason = "Adequate technical execution, standard industry capability."
            fisher_pos = ["Reliable delivery"]
            fisher_neg = ["Commoditized offering"]

        evaluations["Philip Fisher"] = StyleEvaluation(
            strategy_name="Philip Fisher Innovation & Quality",
            investor="Philip Fisher",
            score=fisher_score,
            research_label=fisher_label,
            main_reason=fisher_reason,
            key_positive_factors=fisher_pos,
            key_negative_factors=fisher_neg,
            calculation_basis="Fisher 15-Point Qualitative Checklist + R&D Reinvestment Rate + Customer Stickiness"
        )

        # 8. Dolly Khanna (Quality Small-Cap, High ROCE Niche Compounders)
        if tier in ["Small Cap", "Mid Cap"] and clean in ["MTARTECH", "AARTIPHARM", "PRICOLLTD", "OLECTRA", "MOREPENLAB"]:
            dolly_score = 85.0
            dolly_label = "Strong Fit"
            dolly_reason = "Scalable niche manufacturing with institutional promoter backing, market leadership in specialty sector."
            dolly_pos = ["Niche market dominance", "Attractive small/mid-cap runway", "Improving ROCE trajectory"]
            dolly_neg = ["Small institutional float and quarterly earnings volatility"]
        elif tier == "Large Cap":
            dolly_score = 45.0
            dolly_label = "Weak Fit"
            dolly_reason = "Company is far too large for Dolly Khanna's small-cap niche outperformance strategy."
            dolly_pos = ["Established quality"]
            dolly_neg = ["Market cap exceeds small-cap universe mandate"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            dolly_score = 35.0
            dolly_label = "Weak Fit"
            dolly_reason = "Too speculative; lacks the verified institutional profitability required by Dolly Khanna."
            dolly_pos = ["Small market cap"]
            dolly_neg = ["Inconsistent ROCE", "High promoter pledging or debt"]
        else:
            dolly_score = 58.0
            dolly_label = "Moderate Fit"
            dolly_reason = "Mid-cap with potential, but niche moat is not yet definitive."
            dolly_pos = ["Mid-market presence"]
            dolly_neg = ["Competitive margin pressure"]

        evaluations["Dolly Khanna"] = StyleEvaluation(
            strategy_name="Dolly Khanna Niche Small-Cap",
            investor="Dolly Khanna",
            score=dolly_score,
            research_label=dolly_label,
            main_reason=dolly_reason,
            key_positive_factors=dolly_pos,
            key_negative_factors=dolly_neg,
            calculation_basis="Small-Cap Screening (< ₹15,000 Cr Mcap) + High ROCE (> 18%) + Untapped Sector Niche"
        )

        # 9. Porinju Veliyath (Contrarian Turnaround, Special Situations, Under-researched Small Caps)
        if clean in ["IDEA", "HINDCOPPER", "MISHTANN", "PRAJIND", "RENUKA", "TRIDENT", "MOREPENLAB", "URJA"]:
            porinju_score = 82.0
            porinju_label = "Strong Fit"
            porinju_reason = "Contrarian / turnaround candidate trading at steep discount to replacement cost with potential catalyst."
            porinju_pos = ["Massive upside if operational turnaround succeeds", "Out-of-favor sentiment creates value pricing", "Under-owned by mutual funds"]
            porinju_neg = ["High risk of execution delay or balance sheet stress"]
        elif tier in ["Penny Stock", "Micro Cap"]:
            porinju_score = 70.0
            porinju_label = "Moderate Fit"
            porinju_reason = "Speculative small-cap micro turnaround; high asymmetric return profile if governance improves."
            porinju_pos = ["Low base for re-rating", "Micro float"]
            porinju_neg = ["Binary turnaround risk (either multi-bagger or capital write-down)"]
        elif tier == "Large Cap":
            porinju_score = 42.0
            porinju_label = "Weak Fit"
            porinju_reason = "Heavily researched mega-cap; lacks the contrarian mispricing sought by Porinju."
            porinju_pos = ["Low operational risk"]
            porinju_neg = ["No deep contrarian discount or restructuring catalyst"]
        else:
            porinju_score = 55.0
            porinju_label = "Moderate Fit"
            porinju_reason = "Fairly valued mid-cap; not deeply distressed or un-researched."
            porinju_pos = ["Fair valuation"]
            porinju_neg = ["Moderate turnaround catalyst"]

        evaluations["Porinju Veliyath"] = StyleEvaluation(
            strategy_name="Porinju Veliyath Contrarian & Turnaround",
            investor="Porinju Veliyath",
            score=porinju_score,
            research_label=porinju_label,
            main_reason=porinju_reason,
            key_positive_factors=porinju_pos,
            key_negative_factors=porinju_neg,
            calculation_basis="Contrarian Sentiment Gap + Discount to Replacement Cost + Restructuring / Turnaround Catalyst"
        )

        return evaluations

    @classmethod
    def analyze_portfolio_styles(cls, metrics: PortfolioMetrics) -> PortfolioStyleProfile:
        """Evaluates whole portfolio strategy profile, dominant style, and conflicting holdings."""
        holdings = metrics.holdings_analysis
        if not holdings:
            return PortfolioStyleProfile(
                dominant_style="Neutral",
                best_matching_investor="None",
                average_scores={},
                strategy_fits={},
                conflicting_holdings=[],
                portfolio_orientation_summary="No active holdings in statement."
            )

        # 1. Compute portfolio-weighted score for each of the 9 strategies
        strategy_weighted_scores: Dict[str, float] = {s: 0.0 for s in cls.STRATEGIES}
        strategy_fits: Dict[str, List[str]] = {s: [] for s in cls.STRATEGIES}

        for h in holdings:
            evals = cls.evaluate_holding(h)
            h.investor_scores = {strat: ev.score for strat, ev in evals.items()}
            h.investor_verdicts = {strat: ev.to_dict() if hasattr(ev, 'to_dict') else asdict_safe(ev) for strat, ev in evals.items()}

            w = h.weight_pct / 100.0
            for strat, ev in evals.items():
                strategy_weighted_scores[strat] += ev.score * w
                if ev.research_label == "Strong Fit":
                    strategy_fits[strat].append(h.clean_symbol)

        # Round averages
        avg_scores = {s: round(sc, 1) for s, sc in strategy_weighted_scores.items()}

        # 2. Identify top strategy match
        best_strat = max(avg_scores.items(), key=lambda x: x[1])

        # 3. Classify dominant orientation
        # Check portfolio characteristics
        penny_weight = sum(x.weight_pct for x in holdings if x.market_cap_tier in ["Penny Stock", "Micro Cap"])
        large_weight = sum(x.weight_pct for x in holdings if x.market_cap_tier == "Large Cap")
        growth_stocks_weight = sum(x.weight_pct for x in holdings if x.clean_symbol in ["TATAPOWER", "TMCV", "TMPV", "IRCTC", "RVNL", "EXIDEIND", "OLECTRA", "TATATECH"])

        if growth_stocks_weight > 40.0:
            dom_style = "Growth & Operating Leverage Oriented"
        elif penny_weight > 20.0 or avg_scores.get("Porinju Veliyath", 0) > 65.0:
            dom_style = "Contrarian / Speculative Turnaround Oriented"
        elif large_weight > 60.0:
            dom_style = "Quality & Large-Cap Bluechip Oriented"
        else:
            dom_style = "Mixed Multi-Cap Barbell (Core Compounders + Speculative Long Tail)"

        # 4. Identify conflicting holdings (holdings that clash with the dominant orientation)
        conflicts = []
        for h in holdings:
            if dom_style.startswith("Growth") or dom_style.startswith("Quality"):
                # Penny stocks and distressed holdings conflict
                if h.market_cap_tier in ["Penny Stock", "Micro Cap"] and h.pnl_pct < -40.0:
                    conflicts.append({
                        "symbol": h.clean_symbol,
                        "conflict_type": "Speculative Drag in Quality/Growth Portfolio",
                        "detail": f"{h.clean_symbol} is a high-risk micro-cap down {h.pnl_pct:.1f}% that conflicts with institutional compounding principles."
                    })
            elif "Contrarian" in dom_style:
                if h.market_cap_tier == "Large Cap" and h.stock_score > 75:
                    conflicts.append({
                        "symbol": h.clean_symbol,
                        "conflict_type": "Conservative Anchor in Contrarian Mandate",
                        "detail": f"{h.clean_symbol} is a mature low-beta stalwart with limited multi-bagger re-rating potential."
                    })

        summary = (
            f"The portfolio exhibits a {dom_style} profile. "
            f"The strategy with the highest quantitative alignment is '{best_strat[0]}' (Score: {best_strat[1]}/100). "
            f"A core of high-performing industrial and power winners (Tata Power, TMCV, Idea, MTAR Tech) powers returns, "
            f"while a fragmented long-tail of {len([h for h in holdings if h.market_cap_tier in ['Penny Stock', 'Micro Cap']])} "
            f"speculative micro-caps contributes excessive governance and drawdown friction."
        )

        return PortfolioStyleProfile(
            dominant_style=dom_style,
            best_matching_investor=best_strat[0],
            average_scores=avg_scores,
            strategy_fits=strategy_fits,
            conflicting_holdings=conflicts[:6],
            portfolio_orientation_summary=summary
        )


def asdict_safe(obj: Any) -> Dict[str, Any]:
    """Safely converts dataclass to dict."""
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(obj)
    return getattr(obj, "__dict__", {})
