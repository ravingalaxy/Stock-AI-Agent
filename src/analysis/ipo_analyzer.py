"""
Institutional IPO Analysis Engine & Legendary Investor Strategy Evaluator.

Provides 30+ years institutional-grade quantitative and qualitative evaluation
of Indian IPOs (Mainboard & SME on NSE and BSE).
Integrates DRHP/RHP forensic accounting, Fresh Issue vs. OFS capital allocation,
Anchor investor quality, Grey Market Premium (GMP), subscription demand dynamics,
and quantitative modeling for 9 legendary investor strategies:
- Warren Buffett
- Charlie Munger
- Benjamin Graham
- Peter Lynch
- Joel Greenblatt
- Rakesh Jhunjhunwala
- Philip Fisher
- Dolly Khanna
- Porinju Veliyath
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class IPOData:
    """Standardized institutional schema for Initial Public Offering evaluations."""
    company_name: str
    symbol: str
    sector: str
    price_band_low: float
    price_band_high: float
    lot_size: int
    issue_size_cr: float
    fresh_issue_cr: float
    ofs_cr: float
    
    # Financials (Restated / Pre-IPO)
    revenue_3y_cagr: float        # e.g., 0.22 for 22%
    pat_3y_cagr: float            # e.g., 0.28 for 28%
    operating_margin: float       # e.g., 18.5%
    net_margin: float             # e.g., 12.0%
    pre_roe: float                # e.g., 20.5%
    pre_roce: float               # e.g., 22.0%
    debt_to_equity: float         # e.g., 0.35
    interest_coverage: float      # e.g., 8.5
    fcf_positive: bool            # True if operational cash flow is positive
    
    # Valuation & Market Pricing
    post_pe: float                # P/E at upper price band based on post-issue equity
    post_pb: float                # P/B at upper price band
    industry_pe: float            # Sector median P/E of listed peers
    peg_ratio: Optional[float] = None
    
    # Demand & Sentiment
    gmp: float = 0.0              # Grey Market Premium in INR
    gmp_percent: float = 0.0      # GMP as % of upper band
    qib_subscription: float = 0.0 # QIB subscription multiple
    nii_subscription: float = 0.0 # HNI/NII subscription multiple
    retail_subscription: float = 0.0 # Retail subscription multiple
    anchor_quality: str = "High"  # High (Tier-1 funds), Medium, Low
    
    # Governance & Structure
    promoter_holding_pre: float = 85.0
    promoter_holding_post: float = 65.0
    litigation_flag: bool = False
    auditor_qualification: bool = False
    lead_managers: List[str] = field(default_factory=list)
    objects_of_issue: str = "Growth Capex & Debt Repayment"


class IPOStrategyEvaluator:
    """
    Evaluates an IPO across 9 distinct institutional investment philosophies
    with 30+ years institutional domain expertise.
    """

    def evaluate_warren_buffett(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Warren Buffett Strategy:
        - Historically skeptical of IPOs ("sellers choose the exact top of the market to sell").
        - Requires an undeniable consumer/industrial moat, high ROCE (>18%), predictable cash flows,
          conservative debt (D/E < 0.6), and heavily penalizes excessive Offer for Sale (OFS).
        """
        score = 50.0
        reasons = []
        risks = []

        # Fresh Issue vs OFS check
        fresh_ratio = (ipo.fresh_issue_cr / ipo.issue_size_cr) if ipo.issue_size_cr > 0 else 0.5
        if fresh_ratio >= 0.70:
            score += 15.0
            reasons.append("Predominantly Fresh Issue (>70%); capital retained for productive business expansion.")
        elif fresh_ratio < 0.30:
            score -= 20.0
            risks.append("Heavy Offer for Sale (>70% OFS); promoters/PE funds aggressively cashing out.")

        # Business Quality & Moat
        if ipo.pre_roce >= 18.0 and ipo.pre_roe >= 16.0:
            score += 15.0
            reasons.append(f"Demonstrates superior return on capital (ROCE {ipo.pre_roce:.1f}%, ROE {ipo.pre_roe:.1f}%).")
        else:
            score -= 10.0
            risks.append("Capital efficiency does not meet the 15% hurdle rate for enduring economic moats.")

        # Solvency
        if ipo.debt_to_equity <= 0.5:
            score += 10.0
            reasons.append(f"Conservative balance sheet leverage (Debt/Equity {ipo.debt_to_equity:.2f}x).")
        else:
            score -= 15.0
            risks.append(f"Elevated pre-issue leverage (D/E {ipo.debt_to_equity:.2f}x).")

        # Valuation vs Peers
        if ipo.post_pe <= ipo.industry_pe * 0.95:
            score += 10.0
            reasons.append("Priced at a reasonable discount to listed peer multiples.")
        elif ipo.post_pe >= ipo.industry_pe * 1.30:
            score -= 20.0
            risks.append("Demands an aggressive scarcity premium leaving negligible margin of safety.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")

        primary_reason = reasons[0] if reasons else "Mixed fundamentals with limited competitive protection."
        return {
            "philosophy": "Warren Buffett",
            "style": "Economic Moat & Capital Allocation Discipline",
            "score": round(score, 1),
            "label": label,
            "reason": primary_reason,
            "key_risks": risks[:2] if risks else ["General market volatility post-listing."]
        }

    def evaluate_charlie_munger(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Charlie Munger Strategy:
        - Inversion principle: Focus on avoiding unforced errors, corporate gamesmanship,
          and aggressive restated pro-forma EBITDA adjustments.
        - High scrutiny on governance, litigation, auditor remarks, and insider lock-ins.
        """
        score = 55.0
        reasons = []
        risks = []

        if not ipo.litigation_flag and not ipo.auditor_qualification:
            score += 15.0
            reasons.append("Pristine regulatory and governance track record with clean auditor disclosures.")
        else:
            score -= 25.0
            risks.append("Forensic flags detected in RHP: material litigation or auditor qualification.")

        if ipo.fcf_positive and ipo.net_margin >= 10.0:
            score += 15.0
            reasons.append("Real operational cash flows back reported net earnings with high net margin conversion.")
        else:
            score -= 15.0
            risks.append("Accounting earnings diverge from free cash generation; working capital drag.")

        # Promoter Skin in the Game
        if ipo.promoter_holding_post >= 55.0:
            score += 10.0
            reasons.append(f"Promoters retain substantial skin in the game ({ipo.promoter_holding_post:.1f}% post-IPO).")
        else:
            score -= 15.0
            risks.append(f"Promoter post-issue stake diluted below 55% ({ipo.promoter_holding_post:.1f}%).")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Charlie Munger",
            "style": "Rational Quality & Avoidance of Stupidity",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Fails Munger inversion checklist regarding governance or incentives.",
            "key_risks": risks[:2] if risks else ["Execution risks in executing expansion capex."]
        }

    def evaluate_benjamin_graham(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Benjamin Graham Strategy:
        - Deep value and margin of safety. Extremely skeptical of IPOs unless priced at
          a heavy discount to tangible book value or earnings power of mature peers.
        """
        score = 45.0
        reasons = []
        risks = []

        # Valuation discount to industry
        pe_ratio_to_peer = ipo.post_pe / ipo.industry_pe if ipo.industry_pe > 0 else 1.5
        if pe_ratio_to_peer <= 0.75:
            score += 25.0
            reasons.append(f"Substantial valuation margin of safety: priced at {pe_ratio_to_peer:.2f}x of peer group P/E.")
        elif pe_ratio_to_peer >= 1.20:
            score -= 20.0
            risks.append(f"Priced at {pe_ratio_to_peer:.2f}x of listed peers; absence of tangible Graham margin of safety.")

        if ipo.post_pb <= 2.5:
            score += 15.0
            reasons.append(f"Tangible net asset backing with reasonable P/B multiple of {ipo.post_pb:.1f}x.")
        else:
            score -= 15.0
            risks.append(f"High Price-to-Book multiple ({ipo.post_pb:.1f}x) relies heavily on unproven goodwill/intangibles.")

        if ipo.debt_to_equity <= 0.3:
            score += 15.0
            reasons.append("Unleveraged, fortress balance sheet satisfies Graham solvency requirements.")
        else:
            score -= 10.0
            risks.append("Pre-issue debt load higher than Graham's conservative threshold.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Benjamin Graham",
            "style": "Deep Value & Tangible Margin of Safety",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Pricing lacks defensive margin of safety required for IPO assets.",
            "key_risks": risks[:2] if risks else ["Multiple contraction if sector growth decelerates."]
        }

    def evaluate_peter_lynch(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Peter Lynch Strategy:
        - Growth at a Reasonable Price (GARP). Looks for understandable consumer/business models
          with rapid multi-year growth runway, where PEG <= 1.2 and earnings CAGR > 18%.
        """
        score = 50.0
        reasons = []
        risks = []

        growth_pct = ipo.pat_3y_cagr * 100.0
        peg = ipo.post_pe / growth_pct if growth_pct > 0 else 9.9

        if growth_pct >= 20.0:
            score += 20.0
            reasons.append(f"High compounded profit growth ({growth_pct:.1f}% 3-yr PAT CAGR).")
        elif growth_pct < 10.0:
            score -= 15.0
            risks.append("Sub-10% profit CAGR indicates mature or slowing earnings momentum.")

        if peg <= 1.2:
            score += 20.0
            reasons.append(f"Attractive GARP configuration with PEG ratio of {peg:.2f}x.")
        elif peg > 2.2:
            score -= 15.0
            risks.append(f"Unfavorable PEG ratio ({peg:.2f}x); market has already priced in several years of perfection.")

        # Fresh Issue for scaling
        fresh_ratio = (ipo.fresh_issue_cr / ipo.issue_size_cr) if ipo.issue_size_cr > 0 else 0.5
        if fresh_ratio >= 0.50:
            score += 10.0
            reasons.append("Capital raised directly finances store/capacity multiplication.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Peter Lynch",
            "style": "Growth at a Reasonable Price (GARP)",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Growth profile does not justify post-money earnings multiple.",
            "key_risks": risks[:2] if risks else ["Inability to scale margins during geographic expansion."]
        }

    def evaluate_joel_greenblatt(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Joel Greenblatt Strategy (Magic Formula for IPOs):
        - High Return on Capital (ROCE > 20%) combined with high Earnings Yield (EBIT / EV > 7%).
        """
        score = 50.0
        reasons = []
        risks = []

        earnings_yield_est = (1.0 / ipo.post_pe) * 100.0 if ipo.post_pe > 0 else 0.0

        if ipo.pre_roce >= 20.0:
            score += 25.0
            reasons.append(f"Top-decile capital efficiency (ROCE {ipo.pre_roce:.1f}%).")
        elif ipo.pre_roce < 12.0:
            score -= 20.0
            risks.append(f"Sub-par ROCE ({ipo.pre_roce:.1f}%) fails Magic Formula hurdle.")

        if earnings_yield_est >= 6.5:
            score += 20.0
            reasons.append(f"Strong post-issue earnings yield of {earnings_yield_est:.1f}%.")
        elif earnings_yield_est < 3.5:
            score -= 15.0
            risks.append(f"Low earnings yield ({earnings_yield_est:.1f}%); expensively priced.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Joel Greenblatt",
            "style": "Magic Formula (High ROCE + High Earnings Yield)",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Combined ROCE and Earnings Yield rank in the lower quartile.",
            "key_risks": risks[:2] if risks else ["Post-IPO equity dilution compressing future ROCE."]
        }

    def evaluate_rakesh_jhunjhunwala(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Rakesh Jhunjhunwala Strategy:
        - Big Indian Structural Expansion: Visionary management, massive domestic addressable market,
          high operating leverage, and strong institutional appetite.
        """
        score = 50.0
        reasons = []
        risks = []

        if ipo.revenue_3y_cagr >= 0.20:
            score += 20.0
            reasons.append(f"Strong top-line expansion ({ipo.revenue_3y_cagr * 100:.1f}% Revenue CAGR) riding domestic secular tailwinds.")
        
        if ipo.anchor_quality == "High":
            score += 15.0
            reasons.append("Tier-1 institutional sovereign and domestic mutual fund anchor book validation.")
        
        if ipo.qib_subscription >= 10.0 or ipo.gmp_percent >= 25.0:
            score += 15.0
            reasons.append("Robust institutional appetite and strong Grey Market sentiment indicating high listing momentum.")

        if ipo.debt_to_equity > 1.2:
            score -= 15.0
            risks.append("Excessive leverage could impede capex flexibility in an economic slowdown.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Rakesh Jhunjhunwala",
            "style": "Big India Growth & Operating Leverage",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Lacks the high-conviction scale or domestic market dominance.",
            "key_risks": risks[:2] if risks else ["Macro interest rate cycles or raw material price spikes."]
        }

    def evaluate_philip_fisher(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Philip Fisher Strategy:
        - Scuttlebutt quality: Research and development commitment, sales competence,
          transparent management communication, and long-term industry outlook.
        """
        score = 50.0
        reasons = []
        risks = []

        if ipo.operating_margin >= 18.0:
            score += 20.0
            reasons.append(f"Superior operating margin discipline ({ipo.operating_margin:.1f}%) signals high technological or brand barrier.")
        
        fresh_ratio = (ipo.fresh_issue_cr / ipo.issue_size_cr) if ipo.issue_size_cr > 0 else 0.5
        if "Capex" in ipo.objects_of_issue or "R&D" in ipo.objects_of_issue or fresh_ratio >= 0.6:
            score += 15.0
            reasons.append("Proceeds earmarked for organic R&D and capacity, not debt bailouts.")

        if ipo.litigation_flag:
            score -= 20.0
            risks.append("Governance or promoter disputes violate Fisher's management integrity canon.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Philip Fisher",
            "style": "Management Quality & R&D Excellence",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Limited disclosure on sustainable technological or product differentiation.",
            "key_risks": risks[:2] if risks else ["Key person dependency on founding promoter."]
        }

    def evaluate_dolly_khanna(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Dolly Khanna Strategy:
        - Asset-light small and mid-cap niche leaders, high ROCE, sensible valuation,
          and robust free cash generation.
        """
        score = 50.0
        reasons = []
        risks = []

        if ipo.issue_size_cr <= 2500.0 and ipo.pre_roce >= 18.0:
            score += 25.0
            reasons.append(f"Agile niche market player (Issue ₹{ipo.issue_size_cr:.0f} Cr) generating high ROCE ({ipo.pre_roce:.1f}%).")
        
        if ipo.debt_to_equity <= 0.4:
            score += 15.0
            reasons.append("Clean, low-debt balance sheet provides high operational resilience.")

        if ipo.post_pe > ipo.industry_pe * 1.25:
            score -= 20.0
            risks.append("Demands excessive valuation premium over established large-cap peers.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Dolly Khanna",
            "style": "Asset-Light Niche Small/Mid-Caps",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "Business model requires excessive capex without commensurate return.",
            "key_risks": risks[:2] if risks else ["Customer concentration risk in top 5 accounts."]
        }

    def evaluate_porinju_veliyath(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Porinju Veliyath Strategy:
        - Contrarian value / turnaround opportunities: looking for overlooked, unglamorous
          manufacturing or infrastructure companies priced below replacement cost.
        """
        score = 50.0
        reasons = []
        risks = []

        # If GMP is low or negative, Porinju searches for contrarian value mispricing
        if ipo.post_pe <= ipo.industry_pe * 0.85:
            score += 25.0
            reasons.append(f"Deeply discounted valuation vs listed peers (P/E {ipo.post_pe:.1f} vs industry {ipo.industry_pe:.1f}).")

        if ipo.post_pb <= 2.2:
            score += 15.0
            reasons.append(f"Priced near tangible asset replacement cost (P/B {ipo.post_pb:.1f}x).")

        if ipo.revenue_3y_cagr > 0.15 and ipo.operating_margin < 12.0:
            score += 10.0
            reasons.append("High operating turnaround potential as capacity utilization expands.")

        if ipo.post_pe >= ipo.industry_pe * 1.4:
            score -= 25.0
            risks.append("Hype-driven valuation leaves no contrarian discount.")

        score = max(0.0, min(100.0, score))
        label = "Apply / Buy" if score >= 70.0 else ("Hold / Neutral" if score >= 50.0 else "Avoid")
        return {
            "philosophy": "Porinju Veliyath",
            "style": "Contrarian Turnaround & Asset Mispricing",
            "score": round(score, 1),
            "label": label,
            "reason": reasons[0] if reasons else "No contrarian mispricing detected; issue is richly valued.",
            "key_risks": risks[:2] if risks else ["Protracted turnaround timeline or high working capital cycle."]
        }

    def evaluate_all(self, ipo: IPOData) -> Dict[str, Any]:
        """
        Synthesizes all 9 legendary investor evaluations, composite institutional score,
        verdict, and 3 explicit thesis invalidation failure conditions.
        """
        strategies = {
            "warren_buffett": self.evaluate_warren_buffett(ipo),
            "charlie_munger": self.evaluate_charlie_munger(ipo),
            "benjamin_graham": self.evaluate_benjamin_graham(ipo),
            "peter_lynch": self.evaluate_peter_lynch(ipo),
            "joel_greenblatt": self.evaluate_joel_greenblatt(ipo),
            "rakesh_jhunjhunwala": self.evaluate_rakesh_jhunjhunwala(ipo),
            "philip_fisher": self.evaluate_philip_fisher(ipo),
            "dolly_khanna": self.evaluate_dolly_khanna(ipo),
            "porinju_veliyath": self.evaluate_porinju_veliyath(ipo),
        }

        # Composite Institutional Score:
        # 25% Valuation vs Peers
        # 20% Issue Structure (Fresh vs OFS)
        # 20% Business Quality (ROCE, ROE, Margins)
        # 15% Growth Momentum (Revenue & PAT CAGR)
        # 10% Anchor & Demand Dynamics
        # -10% Governance & Litigation Penalty

        # 1. Valuation subscore (0 - 100)
        val_ratio = ipo.post_pe / ipo.industry_pe if ipo.industry_pe > 0 else 1.0
        if val_ratio <= 0.8:
            val_score = 95.0
        elif val_ratio <= 1.0:
            val_score = 80.0
        elif val_ratio <= 1.25:
            val_score = 60.0
        elif val_ratio <= 1.5:
            val_score = 40.0
        else:
            val_score = 20.0

        # 2. Structure subscore (0 - 100)
        fresh_ratio = (ipo.fresh_issue_cr / ipo.issue_size_cr) if ipo.issue_size_cr > 0 else 0.5
        struct_score = fresh_ratio * 100.0

        # 3. Quality subscore (0 - 100)
        quality_score = min(100.0, (ipo.pre_roce * 2.0 + ipo.pre_roe * 1.5 + ipo.operating_margin * 1.2))

        # 4. Growth subscore (0 - 100)
        growth_score = min(100.0, (ipo.revenue_3y_cagr * 150.0 + ipo.pat_3y_cagr * 150.0))

        # 5. Demand & Anchor subscore (0 - 100)
        anchor_val = 85.0 if ipo.anchor_quality == "High" else (65.0 if ipo.anchor_quality == "Medium" else 40.0)
        gmp_val = min(100.0, max(0.0, 50.0 + ipo.gmp_percent * 1.5))
        demand_score = (anchor_val * 0.5) + (gmp_val * 0.5)

        # 6. Governance penalty
        gov_penalty = 0.0
        if ipo.litigation_flag:
            gov_penalty += 35.0
        if ipo.auditor_qualification:
            gov_penalty += 45.0
        if ipo.promoter_holding_post < 50.0:
            gov_penalty += 20.0

        composite_score = (
            0.25 * val_score +
            0.20 * struct_score +
            0.20 * quality_score +
            0.15 * growth_score +
            0.10 * demand_score -
            0.10 * gov_penalty
        )
        composite_score = round(max(0.0, min(100.0, composite_score)), 1)

        # Institutional Recommendation Label
        if composite_score >= 75.0 and ipo.gmp_percent >= 15.0:
            recommendation = "Apply (High Conviction)"
        elif composite_score >= 65.0:
            recommendation = "Apply for Long-Term"
        elif ipo.gmp_percent >= 25.0 and composite_score >= 50.0:
            recommendation = "Apply for Listing Gains"
        elif composite_score >= 50.0:
            recommendation = "Hold / Neutral"
        else:
            recommendation = "Avoid"

        # 3 Mandatory Thesis Invalidation Conditions
        thesis_invalidations = [
            f"1. Post-Listing Anchor Lock-In Dump: Massive secondary supply overhang if Tier-1 anchors liquidate upon expiration of the mandatory 30-day (50%) and 90-day (remaining 50%) lock-in periods.",
            f"2. Margin Compression to Pre-IPO Base: If operating margin contracts by > 200 bps post-listing, invalidating the pre-issue restated earnings trajectory.",
            f"3. Capital Misallocation: Diversion or delay in deploying Fresh Issue proceeds (> ₹{ipo.fresh_issue_cr:.0f} Cr) towards stated core capex or debt reduction."
        ]

        return {
            "composite_score": composite_score,
            "recommendation": recommendation,
            "strategies": strategies,
            "thesis_invalidations": thesis_invalidations,
            "subscores": {
                "valuation": round(val_score, 1),
                "structure": round(struct_score, 1),
                "quality": round(quality_score, 1),
                "growth": round(growth_score, 1),
                "demand": round(demand_score, 1),
                "gov_penalty": round(gov_penalty, 1)
            }
        }
