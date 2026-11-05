"""
Top Ten Stock Market Portfolios & Comprehensive Stock-Level Investment Rationales.
Curates Dalal Street's most celebrated Superinvestors (Rakesh Jhunjhunwala, Radhakishan Damani,
Ashish Kacholia, Vijay Kedia, Porinju Veliyath, Mukul Agrawal, Sunil Singhania) and Premier Institutional
Thematic Portfolios (Buffett-Munger High Moat, Infrastructure & Defense Capex, Green Energy & EV Transition).

For every portfolio and every single holding, provides forensic rationale, business moat,
catalysts, and risk surveillance parameters.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.portfolio.portfolio_parser import ParsedPortfolio, ParsedHolding


@dataclass
class TopPortfolioHolding:
    """Represents a single stock holding within a Top 10 Portfolio with deep investment reasoning."""
    symbol: str
    clean_symbol: str
    stock_name: str
    exchange: str
    sector: str
    market_cap_tier: str
    weight_pct: float
    current_price: float
    primary_reason: str              # Core reason why stock was taken
    competitive_moat: str            # Durability & franchise edge
    growth_catalyst: str             # Key catalyst for multi-year alpha
    risk_factor: str                 # Key surveillance risk
    investor_label: str              # e.g. "Anchor Multi-Bagger", "Quality Compounder"
    isin: str = "INE_NOT_SPECIFIED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "clean_symbol": self.clean_symbol,
            "stock_name": self.stock_name,
            "exchange": self.exchange,
            "sector": self.sector,
            "market_cap_tier": self.market_cap_tier,
            "weight_pct": self.weight_pct,
            "current_price": self.current_price,
            "primary_reason": self.primary_reason,
            "competitive_moat": self.competitive_moat,
            "growth_catalyst": self.growth_catalyst,
            "risk_factor": self.risk_factor,
            "investor_label": self.investor_label,
            "isin": self.isin,
        }


@dataclass
class TopMarketPortfolio:
    """Represents one of the Top 10 Portfolios of the Indian Stock Market."""
    id: str
    name: str
    manager_or_style: str
    subtitle: str
    description: str
    category: str                   # "Superinvestor" or "Institutional Thematic"
    icon: str
    dominant_philosophy: str
    risk_level: str                 # "Aggressive", "Moderate Growth", "Conservative Quality"
    typical_holding_horizon: str   # "3-5 Years", "5-10 Years", "Decadal"
    holdings: List[TopPortfolioHolding] = field(default_factory=list)

    @property
    def stock_count(self) -> int:
        return len(self.holdings)

    @property
    def top_holding(self) -> Optional[TopPortfolioHolding]:
        if not self.holdings:
            return None
        return max(self.holdings, key=lambda h: h.weight_pct)

    @property
    def sector_allocation(self) -> Dict[str, float]:
        sec_map = {}
        for h in self.holdings:
            sec_map[h.sector] = round(sec_map.get(h.sector, 0.0) + h.weight_pct, 2)
        return dict(sorted(sec_map.items(), key=lambda x: x[1], reverse=True))

    @property
    def market_cap_allocation(self) -> Dict[str, float]:
        mcap_map = {}
        for h in self.holdings:
            mcap_map[h.market_cap_tier] = round(mcap_map.get(h.market_cap_tier, 0.0) + h.weight_pct, 2)
        return dict(sorted(mcap_map.items(), key=lambda x: x[1], reverse=True))

    def to_parsed_portfolio(self) -> ParsedPortfolio:
        """Converts this portfolio into a ParsedPortfolio instance for seamless analysis."""
        parsed_holdings = []
        assumed_capital = 10_000_000.0  # ₹1 Crore reference portfolio
        for h in self.holdings:
            pos_val = (h.weight_pct / 100.0) * assumed_capital
            qty = max(1, int(pos_val / max(1.0, h.current_price)))
            inv_amt = qty * h.current_price
            parsed_holdings.append(
                ParsedHolding(
                    stock_name=h.stock_name,
                    symbol=f"{h.exchange}:{h.clean_symbol}",
                    clean_symbol=h.clean_symbol,
                    exchange=h.exchange,
                    isin=h.isin,
                    quantity=float(qty),
                    buy_price=round(h.current_price * 0.88, 2),  # Assumed historical entry at 12% lower
                    current_price=h.current_price,
                    invested_amount=round(inv_amt * 0.88, 2),
                    current_value=round(inv_amt, 2),
                    pnl_amount=round(inv_amt * 0.12, 2),
                    pnl_pct=13.64,
                    sector=h.sector
                )
            )

        return ParsedPortfolio(
            filename=f"Top_Portfolio_{self.id.upper()}.csv",
            file_type="model_portfolio",
            statement_date="25-10-2026",
            client_name=self.manager_or_style,
            client_id=f"PORTFOLIO-{self.id.upper()}",
            reported_invested=assumed_capital * 0.88,
            reported_current=assumed_capital,
            reported_pnl=assumed_capital * 0.12,
            holdings=parsed_holdings
        )


class TopPortfoliosRepository:
    """Master repository containing Dalal Street's Top 10 Portfolios with detailed stock rationales."""

    @classmethod
    def sync_portfolio_with_live_prices(cls, portfolio: TopMarketPortfolio) -> None:
        """Synchronizes portfolio holdings with real-time stock quotes from Stock model if available."""
        try:
            from apps.market.models import Stock
            clean_syms = [h.clean_symbol.upper() for h in portfolio.holdings]
            candidates = set(clean_syms)
            candidates.update([f"{s}.NS" for s in clean_syms])
            candidates.update([f"{s}.BO" for s in clean_syms])
            stocks = Stock.objects.filter(symbol__in=candidates)
            price_map = {}
            for s in stocks:
                cs = s.clean_symbol.upper()
                if s.current_price and s.current_price > 0:
                    price_map[cs] = s.current_price
            for h in portfolio.holdings:
                cs = h.clean_symbol.upper()
                if cs in price_map:
                    h.current_price = round(price_map[cs], 2)
        except Exception:
            pass

    @classmethod
    def get_all_portfolios(cls, sync_prices: bool = True) -> List[TopMarketPortfolio]:
        """Returns all Top 10 Portfolios with optional live market price synchronization."""
        ports = [
            cls.rakesh_jhunjhunwala_portfolio(),
            cls.radhakishan_damani_portfolio(),
            cls.ashish_kacholia_portfolio(),
            cls.vijay_kedia_portfolio(),
            cls.porinju_veliyath_portfolio(),
            cls.mukul_agrawal_portfolio(),
            cls.sunil_singhania_portfolio(),
            cls.buffett_munger_india_portfolio(),
            cls.infra_defense_supercycle_portfolio(),
            cls.green_energy_ev_transition_portfolio(),
        ]
        if sync_prices:
            for p in ports:
                cls.sync_portfolio_with_live_prices(p)
        return ports

    @classmethod
    def get_portfolio_by_id(cls, portfolio_id: str, sync_prices: bool = True) -> Optional[TopMarketPortfolio]:
        """Fetches a specific portfolio by slug ID with live market prices."""
        for p in cls.get_all_portfolios(sync_prices=sync_prices):
            if p.id.lower() == portfolio_id.lower():
                return p
        return None

    @classmethod
    def calculate_portfolio_overlap(cls, user_holdings: List[Any]) -> Dict[str, Any]:
        """
        Forensic institutional analysis: measures co-investment alignment between user's holdings
        and Dalal Street's Top 10 Portfolios.
        """
        all_portfolios = cls.get_all_portfolios(sync_prices=False)
        guru_map: Dict[str, List[Dict[str, Any]]] = {}
        for p in all_portfolios:
            for h in p.holdings:
                cs = h.clean_symbol.upper()
                if cs not in guru_map:
                    guru_map[cs] = []
                guru_map[cs].append({
                    "portfolio_id": p.id,
                    "portfolio_name": p.name,
                    "manager": p.manager_or_style,
                    "icon": p.icon,
                    "guru_weight": h.weight_pct,
                    "primary_reason": h.primary_reason,
                    "moat": h.competitive_moat,
                    "catalyst": h.growth_catalyst,
                    "investor_label": h.investor_label,
                })

        matched_holdings = []
        co_invested_weight = 0.0
        guru_overlap_weights: Dict[str, float] = {p.id: 0.0 for p in all_portfolios}

        for uh in user_holdings:
            cs = uh.clean_symbol.upper()
            if cs in guru_map:
                co_invested_weight += uh.weight_pct
                gurus = guru_map[cs]
                for g in gurus:
                    guru_overlap_weights[g["portfolio_id"]] += uh.weight_pct
                matched_holdings.append({
                    "clean_symbol": cs,
                    "stock_name": uh.stock_name,
                    "user_weight": uh.weight_pct,
                    "user_current_value": uh.current_value,
                    "sector": uh.sector,
                    "gurus": gurus,
                    "guru_count": len(gurus),
                })

        # Rank gurus by co-investment overlap
        ranked_gurus = []
        for p in all_portfolios:
            shared_weight = round(guru_overlap_weights.get(p.id, 0.0), 2)
            shared_stocks = [m["clean_symbol"] for m in matched_holdings if any(g["portfolio_id"] == p.id for g in m["gurus"])]
            if shared_stocks:
                ranked_gurus.append({
                    "id": p.id,
                    "name": p.name,
                    "icon": p.icon,
                    "manager": p.manager_or_style,
                    "shared_count": len(shared_stocks),
                    "shared_stocks": shared_stocks,
                    "shared_weight": shared_weight,
                })
        ranked_gurus.sort(key=lambda x: (x["shared_count"], x["shared_weight"]), reverse=True)

        return {
            "matched_holdings": matched_holdings,
            "unique_overlap_count": len(matched_holdings),
            "total_co_invested_pct": round(co_invested_weight, 2),
            "ranked_gurus": ranked_gurus,
            "has_overlap": len(matched_holdings) > 0,
        }

    @classmethod
    def find_stock_across_portfolios(cls, query: str) -> List[Dict[str, Any]]:
        """Searches for any stock ticker or company name across all 10 portfolios."""
        q = query.strip().upper()
        results = []
        for p in cls.get_all_portfolios():
            for h in p.holdings:
                if q in h.clean_symbol.upper() or q in h.stock_name.upper():
                    results.append({
                        "portfolio_id": p.id,
                        "portfolio_name": p.name,
                        "manager": p.manager_or_style,
                        "holding": h,
                    })
        return results

    # =========================================================================
    # 1. RAKESH JHUNJHUNWALA (RARE ENTERPRISES)
    # =========================================================================
    @classmethod
    def rakesh_jhunjhunwala_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="rakesh-jhunjhunwala",
            name="Rakesh Jhunjhunwala (Rare Enterprises)",
            manager_or_style="Rare Enterprises / Estate of Rakesh Jhunjhunwala",
            subtitle="The Big Bull — High Operating Leverage, Domestic Consumption & Financialization",
            description="The portfolio of India's most celebrated investor. Focuses on high operating leverage, secular consumption boom, formalization of retail, and the financialization of Indian household savings.",
            category="Superinvestor",
            icon="🐂",
            dominant_philosophy="Growth at Scale & Operating Leverage",
            risk_level="Aggressive Growth",
            typical_holding_horizon="Multi-Decade Compounders",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:TITAN", clean_symbol="TITAN", stock_name="Titan Company Ltd",
                    exchange="NSE", sector="Consumer Discretionary / Luxury", market_cap_tier="Large Cap",
                    weight_pct=28.0, current_price=3480.0,
                    primary_reason="Flagship anchor holding. Unassailable consumer trust and pricing power in branded gold jewelry (Tanishq), gaining market share from unorganized jewelers.",
                    competitive_moat="Brand monopoly, nationwide retail distribution footprint (900+ stores), and superior inventory turnover with negative working capital in gold leasing.",
                    growth_catalyst="Middle-class wedding demand, rapid tier-2/3 store expansions, and high-margin international jewelry & eyewear scaling.",
                    risk_factor="Volatile gold spot import duty shifts and domestic regulatory controls on gold bullion.",
                    investor_label="Core Multi-Bagger Anchor"
                ),
                TopPortfolioHolding(
                    symbol="NSE:TMCV", clean_symbol="TMCV", stock_name="Tata Motors Commercial Vehicles Ltd",
                    exchange="NSE", sector="Automobile & Commercial Vehicles", market_cap_tier="Large Cap",
                    weight_pct=14.5, current_price=960.0,
                    primary_reason="Dominant market share (>70%) in Indian electric passenger vehicles, robust domestic commercial vehicle cash cows, and JLR turnaround.",
                    competitive_moat="First-mover advantage in indigenous Indian EV ecosystem (Tata Passenger Electric Mobility) backed by group synergies (Tata Power, Tata AutoComp).",
                    growth_catalyst="JLR luxury order book execution, debt reduction toward net-zero auto debt, and demerger unlocking commercial and passenger entities.",
                    risk_factor="Global geopolitical slowdown in Europe/China impacting Jaguar Land Rover luxury deliveries.",
                    investor_label="Operating Leverage Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:METROBRAND", clean_symbol="METROBRAND", stock_name="Metro Brands Ltd",
                    exchange="NSE", sector="Footwear & Premium Retail", market_cap_tier="Mid Cap",
                    weight_pct=10.0, current_price=1180.0,
                    primary_reason="Asset-light specialty footwear retailer with industry-leading store-level EBITDA margins (>30%), zero debt, and exclusive global brand rights.",
                    competitive_moat="Exclusive partnerships with Crocs, Foot Locker, and Fila in India, combined with disciplined store rollout and high inventory velocity.",
                    growth_catalyst="Rapid premiumization in Tier-1/2 urban centers and aggressive expansion of destination athleisure stores.",
                    risk_factor="Rising retail mall rentals and competitive discounting from digital-first D2C footwear entrants.",
                    investor_label="Asset-Light Consumer Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:CRISIL", clean_symbol="CRISIL", stock_name="Crisil Ltd",
                    exchange="NSE", sector="Financial Analytics & Credit Ratings", market_cap_tier="Mid Cap",
                    weight_pct=8.5, current_price=4750.0,
                    primary_reason="S&P Global majority subsidiary with an effective duopoly in Indian bond and corporate credit ratings; massive high-margin cash generator.",
                    competitive_moat="High regulatory entry barriers for credit rating agencies, gold-standard institutional credibility, and pricing power over corporate debt issuers.",
                    growth_catalyst="Deepening Indian corporate bond market, ESG certifications, and offshore research outsourcing to parent S&P Global.",
                    risk_factor="Cyclical slowdown in corporate debt issuance and bank credit ratings during high interest rate regimes.",
                    investor_label="Monopolistic Cash Machine"
                ),
                TopPortfolioHolding(
                    symbol="NSE:STARHEALTH", clean_symbol="STARHEALTH", stock_name="Star Health and Allied Insurance",
                    exchange="NSE", sector="Healthcare & Retail Insurance", market_cap_tier="Mid Cap",
                    weight_pct=7.5, current_price=540.0,
                    primary_reason="India's largest standalone health insurer with structural runway given that less than 15% of Indian citizens have private health insurance.",
                    competitive_moat="Network of 14,000+ cashless network hospitals and a proprietary army of 680,000+ specialized health insurance agents.",
                    growth_catalyst="Post-pandemic awareness of medical inflation, retail policy renewals, and composite license regulatory tailwinds.",
                    risk_factor="Surge in medical claim loss ratios during disease outbreaks and elevated customer acquisition costs.",
                    investor_label="Structural Underpenetration Play"
                ),
                TopPortfolioHolding(
                    symbol="NSE:NCC", clean_symbol="NCC", stock_name="NCC Limited",
                    exchange="NSE", sector="Infrastructure & Construction", market_cap_tier="Small Cap",
                    weight_pct=7.0, current_price=295.0,
                    primary_reason="Premier civil construction EPC player with an all-time high order book (>₹55,000 Cr), significant balance sheet deleveraging, and operating margin expansion.",
                    competitive_moat="Proven execution pedigree in massive water supply (Jal Jeevan Mission), transportation, and smart metering projects.",
                    growth_catalyst="Government capex spending ahead of national infrastructure pipeline targets and monetization of real estate claims.",
                    risk_factor="Working capital delays from state government project disbursements and raw material (steel/cement) price spikes.",
                    investor_label="Capex Cycle Alpha"
                ),
                TopPortfolioHolding(
                    symbol="NSE:CANBK", clean_symbol="CANBK", stock_name="Canara Bank",
                    exchange="NSE", sector="Banking & Financial Services", market_cap_tier="Mid Cap",
                    weight_pct=6.5, current_price=105.0,
                    primary_reason="High-conviction value play on PSU banking cleanup with net NPAs below 1.5%, strong credit growth, and low valuation (P/B < 1.0x).",
                    competitive_moat="Deep retail branch footprint across South India, sovereign-backed deposit trust, and low cost of funds.",
                    growth_catalyst="Treasury gains from bond yields, credit growth in infrastructure and retail lending, and planned subsidiary IPOs.",
                    risk_factor="Macro slippages in agriculture/MSME portfolios and pressure on net interest margins.",
                    investor_label="Deep Value Banking Recovery"
                ),
                TopPortfolioHolding(
                    symbol="NSE:FEDERALBNK", clean_symbol="FEDERALBNK", stock_name="Federal Bank Ltd",
                    exchange="NSE", sector="Private Banking & Fintech Co-Lending", market_cap_tier="Mid Cap",
                    weight_pct=6.5, current_price=185.0,
                    primary_reason="Best-in-class regional private lender with conservative asset underwriting, high NRI remittance deposits, and fintech co-lending leadership.",
                    competitive_moat="Dominant 20%+ market share in India's total inward personal remittances, low CASA volatility, and digital partnerships (Google Pay, Fi).",
                    growth_catalyst="Pan-India commercial banking expansion, credit card scaling, and ROA expansion toward 1.4%.",
                    risk_factor="Executive leadership succession transition and margin competition from larger private banking peers.",
                    investor_label="Consistent Quality Banking Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:FORTIS", clean_symbol="FORTIS", stock_name="Fortis Healthcare Ltd",
                    exchange="NSE", sector="Healthcare & Diagnostics", market_cap_tier="Mid Cap",
                    weight_pct=6.0, current_price=510.0,
                    primary_reason="Pan-India quaternary hospital network under IHH Healthcare professional management, driving ARPOB growth and brownfield capacity additions.",
                    competitive_moat="Established clinical excellence in metros (Delhi-NCR, Mumbai, Bengaluru), coupled with majority ownership of Agilus Diagnostics.",
                    growth_catalyst="Addition of 2,000+ new brownfield beds over 4 years without substantial equity dilution; medical tourism boom.",
                    risk_factor="Legal overhangs from legacy promoters and regulatory price caps on medical procedures/implants.",
                    investor_label="Healthcare Asset Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ESCORTS", clean_symbol="ESCORTS", stock_name="Escorts Kubota Ltd",
                    exchange="NSE", sector="Agricultural Machinery & Engineering", market_cap_tier="Mid Cap",
                    weight_pct=5.5, current_price=3850.0,
                    primary_reason="Strategic partnership with Japanese machinery giant Kubota Corporation, positioning Escorts as Kubota's global manufacturing and export hub.",
                    competitive_moat="Top 3 Indian tractor brand with elite engineering, expanding into heavy construction equipment and railway shock absorbers.",
                    growth_catalyst="Global export of Kubota-branded tractors to North America and Europe, plus Indian farm mechanization demand.",
                    risk_factor="Monsoon vagaries impacting Indian rural agricultural sentiment and tractor purchases.",
                    investor_label="MNC Tech Synergy Play"
                ),
            ]
        )

    # =========================================================================
    # 2. RADHAKISHAN DAMANI (DERIVE INVESTMENTS)
    # =========================================================================
    @classmethod
    def radhakishan_damani_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="radhakishan-damani",
            name="Radhakishan Damani (Derive Investments)",
            manager_or_style="Derive Investments / DMart Founder",
            subtitle="The Low-Cost Retail Titan — Zero Debt, High Asset Velocity & Consumer Moats",
            description="The portfolio of DMart founder Radhakishan Damani, celebrated as Warren Buffett's Indian counterpart. Prioritizes companies with extreme cost leadership, proprietary real estate, zero debt, and high inventory turnover.",
            category="Superinvestor",
            icon="🛒",
            dominant_philosophy="Low-Cost Moats & Deep Value",
            risk_level="Conservative Quality",
            typical_holding_horizon="Permanent Holding Period",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:DMART", clean_symbol="DMART", stock_name="Avenue Supermarts Ltd",
                    exchange="NSE", sector="Retail & Supermarkets", market_cap_tier="Large Cap",
                    weight_pct=52.0, current_price=4100.0,
                    primary_reason="Flagship enterprise created by Damani. Lowest procurement cost, owner-occupied store property model (eliminating store rent inflation), and highest sales per square foot in Indian retail.",
                    competitive_moat="EDLP (Everyday Low Price) model supported by prompt supplier payments (securing 2-3% cash discounts), zero net debt, and disciplined cluster-based store expansion.",
                    growth_catalyst="Store count scaling toward 1,000+ superstores nationwide and DMart Ready e-commerce rollout in high-density metro suburbs.",
                    risk_factor="Quick-commerce (Blinkit, Zepto, Instamart) convenience pressure on urban non-bulk grocery items.",
                    investor_label="Unassailable Retail Monopoly"
                ),
                TopPortfolioHolding(
                    symbol="NSE:VSTIND", clean_symbol="VSTIND", stock_name="VST Industries Ltd",
                    exchange="NSE", sector="Consumer Staples & Tobacco", market_cap_tier="Small Cap",
                    weight_pct=14.0, current_price=330.0,
                    primary_reason="Deep value cash cow with durable rural brand equity (Charminar), high operating margins (>30%), zero debt, and continuous 5%+ dividend yields.",
                    competitive_moat="Severe regulatory barriers forbidding new cigarette advertising or manufacturing licenses in India, shielding incumbents from new competition.",
                    growth_catalyst="Value cigarette consumption growth in semi-urban India and real estate asset monetization in Hyderabad.",
                    risk_factor="Government excise and GST increases on tobacco and municipal anti-smoking restrictions.",
                    investor_label="High-Yield Value Cash Cow"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SUNDARMFIN", clean_symbol="SUNDARMFIN", stock_name="Sundaram Finance Ltd",
                    exchange="NSE", sector="Non-Banking Financial Services", market_cap_tier="Mid Cap",
                    weight_pct=8.5, current_price=4600.0,
                    primary_reason="The gold standard of Indian financial prudence. TVS Group heritage with multi-decade track record of industry-lowest gross NPAs through all credit cycles.",
                    competitive_moat="Deep multi-generation customer relationships with commercial vehicle fleet operators and conservative collateral assessment.",
                    growth_catalyst="Commercial vehicle sales recovery, housing finance subsidiary growth, and mutual fund asset growth.",
                    risk_factor="Prolonged slowdown in freight haulage rates and diesel inflation impacting commercial fleet operators.",
                    investor_label="Conservative Compounding Moat"
                ),
                TopPortfolioHolding(
                    symbol="NSE:TRENT", clean_symbol="TRENT", stock_name="Trent Ltd",
                    exchange="NSE", sector="Apparel Retail & Consumer", market_cap_tier="Large Cap",
                    weight_pct=7.5, current_price=6950.0,
                    primary_reason="India's fastest-growing value fashion powerhouse. Zudio and Westside have revolutionized fast fashion with 15-day design-to-rack cycles.",
                    competitive_moat="Proprietary fast-fashion supply chain, own-label inventory control, zero franchisee leakage, and unmatched inventory turnover.",
                    growth_catalyst="Zudio store rollout across Tier-2/3/4 towns, Star Bazaar grocery scaling, and international store trials in the Middle East.",
                    risk_factor="Rich valuation multiples pricing in multi-year aggressive store addition execution.",
                    investor_label="Hyper-Growth Retail Champion"
                ),
                TopPortfolioHolding(
                    symbol="NSE:INDIACEM", clean_symbol="INDIACEM", stock_name="The India Cements Ltd",
                    exchange="NSE", sector="Cement & Building Materials", market_cap_tier="Small Cap",
                    weight_pct=5.5, current_price=360.0,
                    primary_reason="Strategic value and consolidation play in South Indian cement assets with valuable limestone reserves and plant infrastructure.",
                    competitive_moat="Replacement cost valuation: Building new integrated greenfield cement plants with captive limestone in South India is capital-prohibitive.",
                    growth_catalyst="UltraTech Cement acquisition of promoter stake driving operational turnaround, capacity utilization boost, and power/fuel cost cuts.",
                    risk_factor="Regional cement price wars in Andhra Pradesh and Tamil Nadu.",
                    investor_label="Strategic Asset Consolidation"
                ),
                TopPortfolioHolding(
                    symbol="NSE:UBL", clean_symbol="UBL", stock_name="United Breweries Ltd",
                    exchange="NSE", sector="Beverages & Breweries", market_cap_tier="Mid Cap",
                    weight_pct=4.5, current_price=2050.0,
                    primary_reason="Heineken-controlled national market leader controlling ~50% market share of India's beer industry through the iconic Kingfisher brand.",
                    competitive_moat="Strict state-level excise and retail distribution licensing in India creates insurmountable moats for new brewing entrants.",
                    growth_catalyst="Premium craft beer adoption (Heineken Silver, Ultra Max) and favorable demographic trends with rising disposable incomes.",
                    risk_factor="State government price control delays and periodic excise duty hikes.",
                    investor_label="Consumer Monopoly Franchise"
                ),
                TopPortfolioHolding(
                    symbol="NSE:BLUEDART", clean_symbol="BLUEDART", stock_name="Blue Dart Express Ltd",
                    exchange="NSE", sector="Logistics & Express Air Cargo", market_cap_tier="Mid Cap",
                    weight_pct=3.0, current_price=7450.0,
                    primary_reason="DHL majority-owned premier express air parcel logistics provider; mission-critical for high-value e-commerce, banking, and electronics.",
                    competitive_moat="Dedicated Boeing 737 air freighter fleet operating out of 6 major Indian hubs with automated sorting facilities.",
                    growth_catalyst="Fast-growing B2B express surface logistics and high-margin pharmaceutical cold-chain deliveries.",
                    risk_factor="Aviation turbine fuel (ATF) price volatility and airfreight capacity constraints.",
                    investor_label="High-Moat Infrastructure Logistics"
                ),
                TopPortfolioHolding(
                    symbol="NSE:3MINDIA", clean_symbol="3MINDIA", stock_name="3M India Ltd",
                    exchange="NSE", sector="Industrial & Technology Products", market_cap_tier="Mid Cap",
                    weight_pct=2.5, current_price=36200.0,
                    primary_reason="High ROCE (>35%), zero debt Indian arm of Minnesota-based 3M Company, leveraging cutting-edge material science.",
                    competitive_moat="Thousands of proprietary patents in abrasives, adhesives, dental solutions, and automotive reflective sheets.",
                    growth_catalyst="Automotive electronics localization, Indian semiconductor clean-room safety products, and healthcare sterilization.",
                    risk_factor="Royalty fee increases paid to parent 3M US and raw material petrochemical inflation.",
                    investor_label="Ultra-High Quality MNC Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ADVANIHOTR", clean_symbol="ADVANIHOTR", stock_name="Advani Hotels & Resorts (India)",
                    exchange="NSE", sector="Hospitality & Tourism", market_cap_tier="Micro Cap",
                    weight_pct=2.5, current_price=165.0,
                    primary_reason="Debt-free owner of the iconic Caravela Beach Resort in Goa with consistent 100%+ dividend payout track record.",
                    competitive_moat="Pristine South Goa beachfront location where coastal zone regulations prohibit any new competing luxury resort constructions.",
                    growth_catalyst="Surging domestic leisure tourism, destination weddings, and rising average room rates (ARR).",
                    risk_factor="Extreme dependence on a single resort property in Goa.",
                    investor_label="Niche High-Yield Tourism Play"
                ),
            ]
        )

    # =========================================================================
    # 3. ASHISH KACHOLIA (LUCKY INVESTMENT MANAGERS)
    # =========================================================================
    @classmethod
    def ashish_kacholia_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="ashish-kacholia",
            name="Ashish Kacholia (Lucky Investment Managers)",
            manager_or_style="Lucky Investment Managers",
            subtitle="The Small-Cap Whale — High ROCE Niche Leaders & Export Alpha",
            description="Focused on finding early-stage, scalable multi-baggers in small and mid-caps with 20%+ ROCE, high entrepreneurial promoters, and scalable global/domestic niche dominance.",
            category="Superinvestor",
            icon="🐋",
            dominant_philosophy="Small-Cap Alpha & Multi-Baggers",
            risk_level="Aggressive Growth",
            typical_holding_horizon="3-7 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:SAFARI", clean_symbol="SAFARI", stock_name="Safari Industries (India) Ltd",
                    exchange="NSE", sector="Luggage & Travel Accessories", market_cap_tier="Mid Cap",
                    weight_pct=16.0, current_price=2320.0,
                    primary_reason="Disruptive market share gainer in luggage retail, capturing youth and travel demand through indigenous manufacturing and modern product aesthetics.",
                    competitive_moat="Fast design iterations, strong supply chain via greenfield halogen/polypropylene plants in Gujarat, and rapid retail EBO rollout.",
                    growth_catalyst="Boom in leisure tourism, airport expansions, and shift from unbranded bags to branded hard-luggage.",
                    risk_factor="Aggressive price competition from market incumbent VIP Industries and international rival Samsonite.",
                    investor_label="Category Market-Share Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SHAILY", clean_symbol="SHAILY", stock_name="Shaily Engineering Plastics Ltd",
                    exchange="NSE", sector="Precision Engineering & Polymers", market_cap_tier="Small Cap",
                    weight_pct=12.0, current_price=820.0,
                    primary_reason="High-precision injection molded components supplier for global blue-chips including IKEA (furniture) and global pharmaceutical giants (pen-injectors).",
                    competitive_moat="US-FDA audited medical device manufacturing facilities with extreme customer switching costs in insulin and GLP-1 auto-injectors.",
                    growth_catalyst="Scale-up of patent-expiring GLP-1 weight-loss drug injection devices and steel-plastic furniture expansion with IKEA.",
                    risk_factor="Client concentration with IKEA and volatility in specialty polymer resin import prices.",
                    investor_label="Precision Export Multi-Bagger"
                ),
                TopPortfolioHolding(
                    symbol="NSE:GRAVITA", clean_symbol="GRAVITA", stock_name="Gravita India Ltd",
                    exchange="NSE", sector="Recycling & ESG Materials", market_cap_tier="Small Cap",
                    weight_pct=11.0, current_price=2180.0,
                    primary_reason="India's largest non-ferrous secondary lead, aluminum, and plastic recycling player benefiting from strict Battery Waste Management Rules (BWMR).",
                    competitive_moat="Global scrap collection network across 30+ countries feeding cost-efficient smelting plants in India and Africa.",
                    growth_catalyst="Mandatory EPR (Extended Producer Responsibility) norms forcing auto battery giants (Exide, Amara Raja) to buy recycled lead.",
                    risk_factor="Volatile London Metal Exchange (LME) lead spot prices affecting inventory valuation.",
                    investor_label="ESG Circular Economy Champion"
                ),
                TopPortfolioHolding(
                    symbol="NSE:GENESYS", clean_symbol="GENESYS", stock_name="Genesys International Corporation",
                    exchange="NSE", sector="Geospatial Mapping & Digital Twins", market_cap_tier="Small Cap",
                    weight_pct=10.0, current_price=780.0,
                    primary_reason="Pioneer 3D digital twin and high-definition geospatial mapping provider for Indian smart cities, telecom corridors, and autonomous navigation.",
                    competitive_moat="Proprietary street-view 360-degree pan-India HD map database partnered with Google Maps and Ministry of Tourism.",
                    growth_catalyst="National Geospatial Policy deregulation, autonomous driving mapping, and smart infrastructure surveying contracts.",
                    risk_factor="High upfront capex on LiDAR sensors and long payment cycles on government mapping contracts.",
                    investor_label="Deep-Tech Digital Asset Play"
                ),
                TopPortfolioHolding(
                    symbol="NSE:BSOFT", clean_symbol="BSOFT", stock_name="Birlasoft Ltd",
                    exchange="NSE", sector="Information Technology Services", market_cap_tier="Mid Cap",
                    weight_pct=9.5, current_price=640.0,
                    primary_reason="CK Birla Group mid-tier IT services firm compounding through enterprise ERP modernization, cloud transformation, and generative AI integrations.",
                    competitive_moat="Deep domain expertise in manufacturing, life sciences, and BFSI verticals with 15%+ sustained EBIT margins.",
                    growth_catalyst="Multi-year deals in cloud ERP migration (SAP, Oracle) and generative AI co-innovation labs.",
                    risk_factor="US enterprise IT spending deceleration and wage inflation for specialized AI architects.",
                    investor_label="Mid-Cap IT Value Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:FCL", clean_symbol="FCL", stock_name="Fineotex Chemical Ltd",
                    exchange="NSE", sector="Specialty Chemicals", market_cap_tier="Small Cap",
                    weight_pct=9.0, current_price=365.0,
                    primary_reason="Leading manufacturer of specialized textile chemicals, pretreatment additives, and eco-friendly cleaning formulations with zero net debt.",
                    competitive_moat="Technical approvals from global apparel brands (H&M, Zara, Levi's) and global collaboration with HealthGuard Australia.",
                    growth_catalyst="Global textile supply chain shift to India and expansion into high-margin oil drilling and water treatment chemicals.",
                    risk_factor="Cyclical slowdown in global apparel retail export volumes.",
                    investor_label="Debt-Free Specialty Chemical Alpha"
                ),
                TopPortfolioHolding(
                    symbol="NSE:TARC", clean_symbol="TARC", stock_name="TARC Limited",
                    exchange="NSE", sector="Luxury Real Estate Development", market_cap_tier="Small Cap",
                    weight_pct=8.5, current_price=215.0,
                    primary_reason="Prime Delhi-NCR ultra-luxury residential developer holding fully paid, unencumbered land parcels in Central and South Delhi.",
                    competitive_moat="Fully owned land banks acquired decades ago at fractional costs, yielding gross development margins exceeding 50%.",
                    growth_catalyst="Pre-sales velocity of ultra-luxury residential towers (TARC Kailasa, TARC Tripundra) catering to high-net-worth buyers.",
                    risk_factor="Construction execution bottlenecks and approvals from urban local authorities.",
                    investor_label="Real Estate Land-Bank Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:RAGHAV", clean_symbol="RAGHAV", stock_name="Raghav Productivity Enhancers Ltd",
                    exchange="NSE", sector="Industrial Minerals & Metallurgy", market_cap_tier="Small Cap",
                    weight_pct=8.0, current_price=1250.0,
                    primary_reason="Global leader in customized quartz-based ramming mass for steel induction furnaces; increases furnace lining life and cuts melting electricity costs.",
                    competitive_moat="Patented high-purity quartz formulations approved by Tata Steel, JSW Steel, and global steel plants; 30%+ ROCE.",
                    growth_catalyst="Transition of global steel foundries from traditional silica to silica ramming mass and global exports to 35+ countries.",
                    risk_factor="Steel industry cyclical production cuts and raw silica mining lease renewals.",
                    investor_label="Niche High-ROCE Monopoly"
                ),
                TopPortfolioHolding(
                    symbol="NSE:NLSL", clean_symbol="NLSL", stock_name="NIIT Learning Systems Ltd",
                    exchange="NSE", sector="Corporate EdTech & Managed Training", market_cap_tier="Small Cap",
                    weight_pct=8.0, current_price=480.0,
                    primary_reason="Global leader in Managed Training Services (MTS) for Fortune 500 multinationals; generates dollar revenues with high 25%+ EBITDA margins.",
                    competitive_moat="Long-term multi-year enterprise contracts with 100% customer retention among top 20 global enterprise clients.",
                    growth_catalyst="Enterprise workforce upskilling in AI, cloud infrastructure, and cybersecurity across North America and Europe.",
                    risk_factor="Enterprise budget freezes during macroeconomic downturns in the US and Europe.",
                    investor_label="Dollar-Revenue Enterprise Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:DLINKINDIA", clean_symbol="DLINKINDIA", stock_name="D-Link (India) Ltd",
                    exchange="NSE", sector="Networking Equipment & 5G Hardware", market_cap_tier="Small Cap",
                    weight_pct=8.0, current_price=510.0,
                    primary_reason="Dominant market share (>35%) in Indian enterprise routers, Ethernet switches, Wi-Fi 6 hardware, and smart surveillance CCTV networks.",
                    competitive_moat="Established nationwide distributor network of 1,000+ partners and debt-free balance sheet with 30%+ ROCE.",
                    growth_catalyst="5G fiberization of Indian telecom towers, smart home automation, and government's 'Make in India' hardware preference.",
                    risk_factor="Intense competition from low-cost Chinese router importers (TP-Link).",
                    investor_label="5G Telecom & Networking Play"
                ),
            ]
        )

    # =========================================================================
    # 4. VIJAY KEDIA (KEDIA SECURITIES)
    # =========================================================================
    @classmethod
    def vijay_kedia_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="vijay-kedia",
            name="Vijay Kedia (Kedia Securities)",
            manager_or_style="Kedia Securities",
            subtitle="The SMILE Framework — Small in size, Medium in experience, Large in aspiration, Extra-large in market potential",
            description="Famous for picking multibaggers early through his proprietary SMILE framework. Focuses on under-researched companies undergoing massive operating leverage and turnaround.",
            category="Superinvestor",
            icon="🎯",
            dominant_philosophy="SMILE Multi-Baggers & Turnarounds",
            risk_level="Aggressive Growth",
            typical_holding_horizon="3-5 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:TEJASNET", clean_symbol="TEJASNET", stock_name="Tejas Networks Ltd",
                    exchange="NSE", sector="Telecom Equipment & 5G Hardware", market_cap_tier="Mid Cap",
                    weight_pct=22.0, current_price=1180.0,
                    primary_reason="Tata Group controlled indigenous telecom equipment champion executing BSNL's pan-India 4G/5G mobile network deployment with massive ₹8,000+ Cr order book.",
                    competitive_moat="End-to-end proprietary optical networking and wireless software stack, backed by Tata Sons' capital and geopolitical bans on Chinese telecom gear.",
                    growth_catalyst="Commercial rollout of BSNL 100,000 4G/5G mobile towers and global exports to emerging telecom operators.",
                    risk_factor="Supply chain semiconductor chip procurement lead times and high working capital requirements.",
                    investor_label="Sovereign Tech Champion"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ELECON", clean_symbol="ELECON", stock_name="Elecon Engineering Co Ltd",
                    exchange="NSE", sector="Industrial Gears & Material Handling", market_cap_tier="Small Cap",
                    weight_pct=17.0, current_price=640.0,
                    primary_reason="India's leading industrial gearbox and custom conveyor systems manufacturer with zero debt and expanding European export reach.",
                    competitive_moat="Custom engineered gearboxes for core industries (steel, cement, defense, marine) with high technical qualification barriers.",
                    growth_catalyst="Global industrial gear replacement cycle and penetration of European OEMs through its Radicon subsidiary.",
                    risk_factor="Cyclical downturn in domestic industrial capex announcements.",
                    investor_label="Capital Goods Multi-Bagger"
                ),
                TopPortfolioHolding(
                    symbol="NSE:VAIBHAVGBL", clean_symbol="VAIBHAVGBL", stock_name="Vaibhav Global Ltd",
                    exchange="NSE", sector="E-Commerce & TV Shopping", market_cap_tier="Small Cap",
                    weight_pct=12.0, current_price=310.0,
                    primary_reason="Vertically integrated low-cost discount fashion jewelry and lifestyle retailer operating 24/7 TV channels and web portals in US, UK, and Germany.",
                    competitive_moat="Low-cost manufacturing hub in Jaipur (India) feeding direct consumer households in Western markets, eliminating middlemen.",
                    growth_catalyst="Expansion into OTA (over-the-air) streaming TV apps (Roku, Apple TV, Amazon Fire) and lifestyle consumer products.",
                    risk_factor="Weak consumer spending in UK and US due to sticky inflation and high shipping logistics costs.",
                    investor_label="Global Direct-to-Consumer Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ATULAUTO", clean_symbol="ATULAUTO", stock_name="Atul Auto Ltd",
                    exchange="NSE", sector="Commercial Vehicles & Electric 3-Wheelers", market_cap_tier="Small Cap",
                    weight_pct=11.0, current_price=575.0,
                    primary_reason="Established three-wheeler OEM scaling up electric passenger and cargo 3-wheelers (Atul Mobili & Energie) with cutting-edge LFP battery packs.",
                    competitive_moat="Deep semi-urban dealership network across Western and Northern India with loyal commercial transport customer base.",
                    growth_catalyst="Last-mile delivery e-commerce boom and mandatory electrification of urban commercial 3-wheelers.",
                    risk_factor="Intense competition from Bajaj Auto and Mahindra in electric 3-wheelers.",
                    investor_label="EV Mobility Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:PATELENG", clean_symbol="PATELENG", stock_name="Patel Engineering Ltd",
                    exchange="NSE", sector="Hydro Power & Tunneling Infrastructure", market_cap_tier="Small Cap",
                    weight_pct=10.0, current_price=54.0,
                    primary_reason="Specialized civil contractor with unmatched historical track record in constructing massive hydroelectric dams, tunnels, and irrigation projects.",
                    competitive_moat="Niche engineering expertise in difficult Himalayan terrains; huge order book exceeding ₹18,000 Cr with central PSUs (NHPC, SJVN).",
                    growth_catalyst="Government's multi-gigawatt pumped hydro storage mandate and monetization of non-core real estate assets to reduce debt.",
                    risk_factor="Geological surprises during tunneling and severe weather delays in Himalayan project sites.",
                    investor_label="Turnaround Infrastructure Asset"
                ),
                TopPortfolioHolding(
                    symbol="NSE:HERITGFOOD", clean_symbol="HERITGFOOD", stock_name="Heritage Foods Ltd",
                    exchange="NSE", sector="Dairy & Value-Added Consumer FMCG", market_cap_tier="Small Cap",
                    weight_pct=8.0, current_price=460.0,
                    primary_reason="South India dairy giant scaling high-margin value-added products (curd, paneer, flavored milk, ghee) with direct milk procurement from 300,000+ farmers.",
                    competitive_moat="Direct cold-chain logistics footprint reaching 1.5 million households every morning, insulated by high consumer brand trust.",
                    growth_catalyst="Rapid margin expansion as value-added dairy share surpasses 35% of overall product revenue mix.",
                    risk_factor="Raw milk procurement price spikes during summer droughts and regional political interference.",
                    investor_label="Consumer FMCG Compounding"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SIYSIL", clean_symbol="SIYSIL", stock_name="Siyaram Silk Mills Ltd",
                    exchange="NSE", sector="Textiles & Menswear Fabric", market_cap_tier="Small Cap",
                    weight_pct=6.5, current_price=490.0,
                    primary_reason="Durable brand recall across Tier-2/3 India for men's suiting and shirting (Siyaram's, J. Hampstead, Oxemberg) with pristine debt-free balance sheet.",
                    competitive_moat="Dominant distribution reach across 100,000+ multi-brand retail textile outlets with high return on capital.",
                    growth_catalyst="Expansion of exclusive brand outlets (EBOs) and ethnic wedding wear market expansion.",
                    risk_factor="Volatile raw material costs (cotton yarn and polyester fiber) and unseasonal weather impacting wedding purchases.",
                    investor_label="Debt-Free Consumer Brand"
                ),
                TopPortfolioHolding(
                    symbol="NSE:INNOVATORS", clean_symbol="INNOVATORS", stock_name="Innovators Facade Systems Ltd",
                    exchange="NSE", sector="Architectural Facade Engineering", market_cap_tier="Micro Cap",
                    weight_pct=5.5, current_price=210.0,
                    primary_reason="India's leading specialized engineering contractor for architectural glass facades for airports, premium IT parks, and luxury high-rises.",
                    competitive_moat="In-house computerized manufacturing facility in Pune and specialized structural glazing design capabilities.",
                    growth_catalyst="National airport expansion program (UDAN) and Grade-A commercial office space construction boom.",
                    risk_factor="Working capital stretch and construction delays on large commercial real estate sites.",
                    investor_label="Niche Engineering Micro-Cap"
                ),
                TopPortfolioHolding(
                    symbol="NSE:AFFORDABLE", clean_symbol="AFFORDABLE", stock_name="Affordable Robotic & Automation",
                    exchange="NSE", sector="Industrial Robotics & Smart Parking", market_cap_tier="Micro Cap",
                    weight_pct=4.5, current_price=480.0,
                    primary_reason="Specialist in robotic welding automation lines for auto OEMs and automated multi-level car parking systems for modern urban housing.",
                    competitive_moat="High custom engineering barrier for turnkey automotive robotic welding lines; long-standing vendor to Mahindra and Tata Motors.",
                    growth_catalyst="Auto OEM capex cycles for new model launches and municipal mandates for automated stack parking in congested metros.",
                    risk_factor="Lumpy order intake and customer concentration in auto manufacturing.",
                    investor_label="Industrial Robotics Automation Play"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SUDARSCHEM", clean_symbol="SUDARSCHEM", stock_name="Sudarshan Chemical Industries",
                    exchange="NSE", sector="Specialty Pigments & Coatings", market_cap_tier="Small Cap",
                    weight_pct=3.5, current_price=1040.0,
                    primary_reason="Acquisition of German rival Heubach creates the world's #2 largest pigment giant with global distribution and cutting-edge color chemistry.",
                    competitive_moat="Supplies mission-critical pigments for automotive coatings, cosmetics, plastics, and printing inks with long qualification lead times.",
                    growth_catalyst="Cost rationalization at European Heubach plants, shifting production to lower-cost Indian manufacturing facilities in Roha.",
                    risk_factor="Debt servicing during integration of the global Heubach acquisition.",
                    investor_label="Global M&A Scale Turnaround"
                ),
            ]
        )

    # =========================================================================
    # 5. PORINJU VELIYATH (EQUITY INTELLIGENCE)
    # =========================================================================
    @classmethod
    def porinju_veliyath_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="porinju-veliyath",
            name="Porinju Veliyath (Equity Intelligence)",
            manager_or_style="Equity Intelligence India",
            subtitle="The Contrarian Value & Turnaround Maestro — Deep Moats at Deep Discounts",
            description="Famous for buying unloved, under-researched companies trading below replacement cost, where corporate governance cleanup or industry cycle turnarounds unlock massive alpha.",
            category="Superinvestor",
            icon="💎",
            dominant_philosophy="Contrarian Turnaround & Value Re-Rating",
            risk_level="Aggressive Contrarian",
            typical_holding_horizon="3-5 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:KERALAYUR", clean_symbol="KERALAYUR", stock_name="Kerala Ayurveda Ltd",
                    exchange="NSE", sector="Ayurvedic Healthcare & Wellness", market_cap_tier="Micro Cap",
                    weight_pct=18.0, current_price=275.0,
                    primary_reason="Turnaround play in traditional herbal medicine and clinical Ayurvedic research; expanding Ayurvedic academy and clinical wellness clinics in the US.",
                    competitive_moat="Authentic 80-year heritage of traditional Kerala Ayurvedic manuscripts, proprietary herbal formulations, and NABH-accredited hospitals.",
                    growth_catalyst="Global adoption of natural plant-based preventive medicine and digital direct-to-consumer wellness supplements.",
                    risk_factor="Small operating base and marketing expenditure needed to establish brand in Western markets.",
                    investor_label="Contrarian Wellness Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ORIENTBELL", clean_symbol="ORIENTBELL", stock_name="Orient Bell Ltd",
                    exchange="NSE", sector="Ceramic Tiles & Home Improvement", market_cap_tier="Small Cap",
                    weight_pct=15.0, current_price=385.0,
                    primary_reason="Beaten-down ceramic tile manufacturer benefiting from plant modernizations, debt reduction, and transition toward high-margin digital glazed vitrified tiles.",
                    competitive_moat="Established dealer network with digital visualization kiosks (Quick Pave) enabling retail customers to preview tile patterns in 3D.",
                    growth_catalyst="Real estate housing completion cycle driving residential flooring replacement demand.",
                    risk_factor="Elevated natural gas fuel prices at Morbi tile clusters impacting manufacturing margins.",
                    investor_label="Home Building Products Re-Rating"
                ),
                TopPortfolioHolding(
                    symbol="NSE:CENTUM", clean_symbol="CENTUM", stock_name="Centum Electronics Ltd",
                    exchange="NSE", sector="Defense & Aerospace EMS", market_cap_tier="Small Cap",
                    weight_pct=14.0, current_price=1620.0,
                    primary_reason="Mission-critical electronics manufacturing services (EMS) provider designing ruggedized microelectronics for ISRO space missions, DRDO missiles, and naval radars.",
                    competitive_moat="Stringent defense space-grade flight-heritage certifications that take 5-10 years for competing contract manufacturers to obtain.",
                    growth_catalyst="ISRO Gaganyaan space missions, domestic defense missile indigenization, and global aerospace offset contracts.",
                    risk_factor="Long government testing and validation cycles delaying revenue recognition.",
                    investor_label="Defense Deep-Tech Alpha"
                ),
                TopPortfolioHolding(
                    symbol="NSE:RPSGVENTS", clean_symbol="RPSGVENTS", stock_name="RPSG Ventures Ltd",
                    exchange="NSE", sector="Holding Company & Tech Services", market_cap_tier="Small Cap",
                    weight_pct=12.0, current_price=840.0,
                    primary_reason="Sanjiv Goenka holding company trading at a massive (>60%) holding company discount to the underlying market value of Firstsource Solutions and FMCG ventures.",
                    competitive_moat="Controls 53% stake in Firstsource Solutions (billion-dollar IT/BPO powerhouse) plus fast-growing healthy snacking brand 'Too Yumm!'.",
                    growth_catalyst="Narrowing of holding company discount through potential business demergers or special dividend payouts.",
                    risk_factor="Holding company discount persistence and losses in nascent digital direct-to-consumer FMCG brands.",
                    investor_label="Deep Value Holding Company Arbitrage"
                ),
                TopPortfolioHolding(
                    symbol="NSE:MAXHEALTH", clean_symbol="MAXHEALTH", stock_name="Max Healthcare Institute",
                    exchange="NSE", sector="Healthcare & Multispecialty Hospitals", market_cap_tier="Large Cap",
                    weight_pct=11.0, current_price=940.0,
                    primary_reason="Institutional-grade compounder in quaternary healthcare; highest ARPOB among listed peers, professional management, and high-margin oncology/cardiology focus.",
                    competitive_moat="Prime metro hospital real estate in Delhi-NCR, Mumbai, and Lucknow with extreme entry barriers for new tertiary hospitals.",
                    growth_catalyst="Adding 4,000+ new beds over the next 4 years through brownfield expansions and accretive hospital acquisitions.",
                    risk_factor="High valuation multiples leaving limited room for operational execution stumbles.",
                    investor_label="Tier-1 Healthcare Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:KAYA", clean_symbol="KAYA", stock_name="Kaya Limited",
                    exchange="NSE", sector="Dermatological Clinics & Skincare", market_cap_tier="Micro Cap",
                    weight_pct=9.0, current_price=390.0,
                    primary_reason="Marico parent heritage dermatology clinic network undergoing strategic restructuring, closing unprofitable branches, and expanding e-commerce product lines.",
                    competitive_moat="Network of 70+ specialized skin and hair clinics staffed by certified dermatologists across India and Middle East.",
                    growth_catalyst="Surging demand for non-invasive cosmetic dermatology, laser treatments, and anti-aging aesthetic procedures.",
                    risk_factor="Historical clinic profitability drag and competition from low-cost aesthetic centers.",
                    investor_label="Clinical Skincare Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:EMAMIPAP", clean_symbol="EMAMIPAP", stock_name="Emami Paper Mills Ltd",
                    exchange="NSE", sector="Paper & Packaging Boards", market_cap_tier="Small Cap",
                    weight_pct=8.0, current_price=125.0,
                    primary_reason="India's largest newsprint and premier multi-layer coated packaging board manufacturer benefiting from the surge in e-commerce and pharmaceutical packaging.",
                    competitive_moat="Massive integrated plant in Balasore (Odisha) with captive power generation and proximity to coal/raw material ports.",
                    growth_catalyst="Single-use plastic bans forcing consumer brands to adopt biodegradable paper packaging board.",
                    risk_factor="Import of cheap paper from ASEAN nations and cyclical spikes in imported recycled wastepaper pulp prices.",
                    investor_label="Cyclical Packaging Asset"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ARVINDFASN", clean_symbol="ARVINDFASN", stock_name="Arvind Fashions Ltd",
                    exchange="NSE", sector="Branded Apparel & Retail", market_cap_tier="Small Cap",
                    weight_pct=7.5, current_price=535.0,
                    primary_reason="India's premier international casualwear brand licensee (US Polo Assn, Tommy Hilfiger, Calvin Klein, Arrow, Flying Machine) turning profitable with debt reduction.",
                    competitive_moat="Unrivaled portfolio of global marquee casualwear brands with high consumer aspiration and pricing power.",
                    growth_catalyst="Expansion of US Polo Assn into kidswear, footwear, and innerwear; double-digit retail same-store sales growth.",
                    risk_factor="Consumer spending slowdown in discretionary fashion apparel.",
                    investor_label="Marquee Brand Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ANSALBUIL", clean_symbol="ANSALBUIL", stock_name="Ansal Buildwell Ltd",
                    exchange="NSE", sector="Real Estate & Land Assets", market_cap_tier="Micro Cap",
                    weight_pct=5.0, current_price=110.0,
                    primary_reason="Contrarian deep-value real estate asset play holding legacy land parcels across NCR, Haryana, and Rajasthan trading at a fraction of market net asset value.",
                    competitive_moat="Low historical land cost basis allowing profitable joint developments or outright land monetization.",
                    growth_catalyst="Monetization of prime non-core land parcels to settle debt and launch plotted township developments.",
                    risk_factor="Illiquid micro-cap trading volumes and prolonged urban municipal land clearance timelines.",
                    investor_label="Deep Value Land Monetization"
                ),
            ]
        )

    # =========================================================================
    # 6. MUKUL AGRAWAL (PARAM CAPITAL)
    # =========================================================================
    @classmethod
    def mukul_agrawal_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="mukul-agrawal",
            name="Mukul Agrawal (Param Capital)",
            manager_or_style="Param Capital",
            subtitle="High-Growth Momentum, Earnings Acceleration & Agile Sector Rotation",
            description="Aggressive growth investor known for early detection of rapid quarterly EBITDA acceleration, capacity debottlenecking, and high-beta momentum across defense, engineering, and specialty pharma.",
            category="Superinvestor",
            icon="🚀",
            dominant_philosophy="Earnings Acceleration & Sector Rotation",
            risk_level="Aggressive Momentum",
            typical_holding_horizon="1-3 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:NEULANDLAB", clean_symbol="NEULANDLAB", stock_name="Neuland Laboratories Ltd",
                    exchange="NSE", sector="Pharma CDMO & Specialty APIs", market_cap_tier="Mid Cap",
                    weight_pct=17.0, current_price=14200.0,
                    primary_reason="Stellar turnaround in Custom Manufacturing (CDMO) for global biotech and pharma innovators; high-margin complex peptides driving exponential profit growth.",
                    competitive_moat="Deep synthetic chemistry capabilities in complex molecules with US-FDA compliant manufacturing sites in Hyderabad.",
                    growth_catalyst="Commercialization of late-phase clinical molecules by global pharmaceutical innovators leading to recurring multi-year commercial supply contracts.",
                    risk_factor="Lumpy quarterly CDMO batch deliveries causing short-term earnings volatility.",
                    investor_label="High-Margin CDMO Super-Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:RAYMOND", clean_symbol="RAYMOND", stock_name="Raymond Ltd",
                    exchange="NSE", sector="Textiles, Real Estate & Aerospace", market_cap_tier="Mid Cap",
                    weight_pct=14.0, current_price=1750.0,
                    primary_reason="Value-unlocking restructuring maestro demerging into pure-play lifestyle apparel, high-margin Thane residential real estate, and precision defense engineering.",
                    competitive_moat="Century-old brand trust in suiting and shirting, coupled with 100+ acres of prime freehold land in Thane (Mumbai).",
                    growth_catalyst="Listing of separate entities (Lifestyle, Real Estate) unlocking trapped conglomerate valuation discount.",
                    risk_factor="Execution of the multi-entity demerger and tax restructuring.",
                    investor_label="Conglomerate Value Demerger"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ZENTEC", clean_symbol="ZENTEC", stock_name="Zen Technologies Ltd",
                    exchange="NSE", sector="Defense Combat Simulators & Anti-Drone", market_cap_tier="Small Cap",
                    weight_pct=13.0, current_price=1810.0,
                    primary_reason="Indigenous pioneer in defense combat training simulators and Counter-Drone (Anti-Drone) Systems with record-breaking domestic and export order books.",
                    competitive_moat="Over 140+ filed patents in simulator technology, defense RF signal jamming, and hard-kill drone counter-measures.",
                    growth_catalyst="Surging global demand for anti-drone air defense following modern drone warfare in Ukraine and Middle East.",
                    risk_factor="Heavy dependence on defense procurement budgetary clearances.",
                    investor_label="Defense Tech Hyper-Growth"
                ),
                TopPortfolioHolding(
                    symbol="NSE:PTCIL", clean_symbol="PTCIL", stock_name="PTC Industries Ltd",
                    exchange="NSE", sector="Titanium Castings & Aerospace Alloys", market_cap_tier="Mid Cap",
                    weight_pct=12.0, current_price=11200.0,
                    primary_reason="Building India's largest titanium and superalloy casting foundry to supply structural components for global jet engines (Safran, Rolls-Royce, GE Aerospace).",
                    competitive_moat="High-tech vacuum arc remelting technology with aerospace certifications replacing Western reliance on Russian titanium.",
                    growth_catalyst="Commercial production from the new Lucknow defense corridor mega-facility for defense aircraft and naval submarines.",
                    risk_factor="High capital intensity and long qualification lead times with global aerospace primes.",
                    investor_label="Aerospace Materials Monopoly"
                ),
                TopPortfolioHolding(
                    symbol="NSE:DISHMAN", clean_symbol="DISHMAN", stock_name="Dishman Carbogen Amcis Ltd",
                    exchange="NSE", sector="Pharma CRAMS & High-Potency APIs", market_cap_tier="Small Cap",
                    weight_pct=9.0, current_price=185.0,
                    primary_reason="Turnaround in global CRAMS assets with cutting-edge high-potency API labs in Switzerland and France overcoming past European inspection hurdles.",
                    competitive_moat="Specialized capability in handling highly potent cytotoxic cancer molecules under sterile containment.",
                    growth_catalyst="Resolution of regulatory audit observations and operational ramp-up of the Bavla commercial formulation plant.",
                    risk_factor="Elevated debt levels on European subsidiaries.",
                    investor_label="Pharma Contract Research Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SURYAROSH", clean_symbol="SURYAROSH", stock_name="Surya Roshni Ltd",
                    exchange="NSE", sector="Steel Pipes & Consumer LED Lighting", market_cap_tier="Small Cap",
                    weight_pct=8.5, current_price=570.0,
                    primary_reason="Major beneficiary of city gas distribution (CGD) network expansion through ERW steel pipes, coupled with debt-free status and consumer lighting cash flows.",
                    competitive_moat="Comprehensive manufacturing footprint in steel pipes and 250,000+ consumer retail lighting touchpoints.",
                    growth_catalyst="Large infrastructure orders for drinking water supply (Jal Jeevan Mission) and oil/gas pipelines.",
                    risk_factor="Fluctuations in hot-rolled steel coil input costs.",
                    investor_label="Capex & Infrastructure Pipes"
                ),
                TopPortfolioHolding(
                    symbol="NSE:GANESHAECO", clean_symbol="GANESHAECO", stock_name="Ganesha Ecosphere Ltd",
                    exchange="NSE", sector="Recycled PET & Sustainable Textiles", market_cap_tier="Small Cap",
                    weight_pct=7.5, current_price=2250.0,
                    primary_reason="India's largest recycled polyester staple fiber (rPET) manufacturer converting discarded plastic bottles into premium yarn for Nike, Adidas, and Zara.",
                    competitive_moat="Nationwide network of 300+ bottle scrap collection centers feeding automated washing and extrusion lines in Warangal.",
                    growth_catalyst="Mandatory global brand pledges to use 50%+ recycled polyester in garments by 2030.",
                    risk_factor="Volatile virgin polyester yarn prices competing with recycled alternatives.",
                    investor_label="Sustainable Circular Economy"
                ),
                TopPortfolioHolding(
                    symbol="NSE:PDS", clean_symbol="PDS", stock_name="PDS Limited",
                    exchange="NSE", sector="Global Apparel Supply Chain Platform", market_cap_tier="Small Cap",
                    weight_pct=7.0, current_price=530.0,
                    primary_reason="Asset-light global design, sourcing, and logistics platform connecting international retailers (Walmart, Target, ASOS) with global garment manufacturers.",
                    competitive_moat="Vast global network of in-house designers, virtual sampling software, and cloud-based factory compliance auditing.",
                    growth_catalyst="Tailwinds from global fashion brands diversifying sourcing away from China toward India, Bangladesh, and Sri Lanka.",
                    risk_factor="Global consumer fashion spending weakness and supply chain ocean freight disruptions.",
                    investor_label="Asset-Light Global Sourcing Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ALLCARGO", clean_symbol="ALLCARGO", stock_name="Allcargo Logistics Ltd",
                    exchange="NSE", sector="Global Freight Forwarding & Logistics", market_cap_tier="Small Cap",
                    weight_pct=6.0, current_price=58.0,
                    primary_reason="World's #1 LCL (less-than-container-load) ocean freight consolidator operating through ECU Worldwide across 180 countries.",
                    competitive_moat="Unrivaled global ocean shipping network with proprietary digital booking platform (ECU360) and ICD network across India.",
                    growth_catalyst="Restructuring and demerger creating focused pure-play international supply chain and domestic express logistics entities.",
                    risk_factor="Cyclical ocean container freight rate collapses and global export contraction.",
                    investor_label="Global Logistics Market Leader"
                ),
                TopPortfolioHolding(
                    symbol="NSE:CAPACITE", clean_symbol="CAPACITE", stock_name="Capacit'e Infraprojects Ltd",
                    exchange="NSE", sector="High-Rise Civil Construction", market_cap_tier="Small Cap",
                    weight_pct=6.0, current_price=375.0,
                    primary_reason="Premier urban building construction EPC specialist for super-high-rise residential towers, multi-specialty hospitals, and commercial campuses.",
                    competitive_moat="Marquee private clientele (Godrej Properties, Oberoi Realty, Lodha) and specialized high-rise automated climbing formwork.",
                    growth_catalyst="Record-breaking residential housing launches across Mumbai, Pune, and Bengaluru.",
                    risk_factor="Working capital delays on public sector hospital construction contracts.",
                    investor_label="Real Estate Construction Capex"
                ),
            ]
        )

    # =========================================================================
    # 7. SUNIL SINGHANIA (ABAKKUS ASSET MANAGER)
    # =========================================================================
    @classmethod
    def sunil_singhania_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="sunil-singhania",
            name="Sunil Singhania (Abakkus Asset Manager)",
            manager_or_style="Abakkus Asset Manager LLP",
            subtitle="The MEP Framework — Management, Earnings, Price with Institutional Governance",
            description="Former Reliance Mutual Fund CIO Sunil Singhania applies his proprietary MEP Framework (Management with integrity, predictable double-digit Earnings growth, and disciplined Price without overpaying) to build high-alpha alpha portfolios.",
            category="Superinvestor",
            icon="⚖️",
            dominant_philosophy="MEP Disciplined Value & Growth",
            risk_level="Moderate Growth",
            typical_holding_horizon="3-5 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:JSL", clean_symbol="JSL", stock_name="Jindal Stainless Ltd",
                    exchange="NSE", sector="Metals & Stainless Steel", market_cap_tier="Mid Cap",
                    weight_pct=18.0, current_price=710.0,
                    primary_reason="Dominant market share (>50%) in Indian stainless steel; lowest-cost integrated producer globally with massive scale in Jajpur and Hisar.",
                    competitive_moat="End-to-end integrated production, captive rail sidings, and broad product spectrum across railway coaches, defense, and architecture.",
                    growth_catalyst="Indian Railways modernization (stainless steel Vande Bharat trains), auto exhaust upgrades, and anti-dumping duties on cheap Chinese imports.",
                    risk_factor="Cyclical volatility in global nickel and ferro-chrome raw material prices.",
                    investor_label="Cost-Leadership Metals Champion"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SARDAEN", clean_symbol="SARDAEN", stock_name="Sarda Energy & Minerals Ltd",
                    exchange="NSE", sector="Metals, Mining & Captive Hydro", market_cap_tier="Small Cap",
                    weight_pct=14.0, current_price=410.0,
                    primary_reason="Ultra-low-cost, debt-free integrated steel, ferroalloys, and power producer with captive iron ore and coal mines plus operational hydropower plants.",
                    competitive_moat="Captive mineral resources and cheap hydro power keep production costs in the lowest global quartile; superior ROCE (>25%).",
                    growth_catalyst="Gare Palma coal mine operationalization and commissioning of new commercial hydropower projects in Sikkim.",
                    risk_factor="Regulatory environmental audits on mining leases and cyclical ferroalloy pricing.",
                    investor_label="Low-Cost Integrated Commodity Moat"
                ),
                TopPortfolioHolding(
                    symbol="NSE:IONEXCHANG", clean_symbol="IONEXCHANG", stock_name="Ion Exchange (India) Ltd",
                    exchange="NSE", sector="Water Treatment & Environmental Engineering", market_cap_tier="Small Cap",
                    weight_pct=12.0, current_price=535.0,
                    primary_reason="Comprehensive water and wastewater treatment solution provider executing large industrial zero-liquid discharge (ZLD) plants and drinking water projects.",
                    competitive_moat="Proprietary INDION ion-exchange resins and membranes with technical approvals across refineries, power plants, and pharma.",
                    growth_catalyst="Government Jal Jeevan Mission rural drinking water projects and stringent global industrial effluent norms.",
                    risk_factor="High working capital intensity and project execution milestone approval delays.",
                    investor_label="Environmental Engineering ESG Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:CMSINFO", clean_symbol="CMSINFO", stock_name="CMS Info Systems Ltd",
                    exchange="NSE", sector="Banking Technology & Cash Management", market_cap_tier="Small Cap",
                    weight_pct=11.0, current_price=590.0,
                    primary_reason="Market leader (>45% market share) in Indian ATM cash management, banking automation, and retail cash collections with recurring annuity cash flows.",
                    competitive_moat="Network of 4,000+ armored cash vans and proprietary routing software creating insurmountable route-density unit economic advantages.",
                    growth_catalyst="Banks outsourcing entire ATM networks (Managed Services) and rapid adoption of AI remote video surveillance in banking branches.",
                    risk_factor="Increasing digital payments (UPI) reducing the total physical currency velocity over the long term.",
                    investor_label="High-Cash-Flow Monopoly Network"
                ),
                TopPortfolioHolding(
                    symbol="NSE:STYLAMIND", clean_symbol="STYLAMIND", stock_name="Stylam Industries Ltd",
                    exchange="NSE", sector="Building Materials & Laminates", market_cap_tier="Small Cap",
                    weight_pct=10.0, current_price=2180.0,
                    primary_reason="Asia's largest single-location decorative laminate manufacturing facility exporting high-pressure laminates to 80+ countries with top-tier EBITDA margins (>20%).",
                    competitive_moat="Massive manufacturing economies of scale, debt-free balance sheet, and direct distribution to European architectural building suppliers.",
                    growth_catalyst="Capacity debottlenecking, expanding domestic dealer network, and launching acrylic solid surface panels.",
                    risk_factor="Raw material chemical costs (phenol, melamine, and craft paper) and ocean container shipping rates.",
                    investor_label="High-Margin Export Compounder"
                ),
                TopPortfolioHolding(
                    symbol="NSE:IIFL", clean_symbol="IIFL", stock_name="IIFL Finance Ltd",
                    exchange="NSE", sector="Non-Banking Financial Services", market_cap_tier="Small Cap",
                    weight_pct=9.0, current_price=430.0,
                    primary_reason="Deep-value recovery play in retail NBFC lending with robust gold loan branch network, microfinance, and affordable housing loan book.",
                    competitive_moat="Thousands of neighborhood gold loan branches providing immediate liquidity against physical gold collateral with near-zero credit loss.",
                    growth_catalyst="Lifting of regulatory operational curbs, restoration of co-lending partnerships, and return to normalized credit growth.",
                    risk_factor="Regulatory scrutiny on gold loan collateral valuation and customer churn.",
                    investor_label="Contrarian Financial Turnaround"
                ),
                TopPortfolioHolding(
                    symbol="NSE:UGROCAP", clean_symbol="UGROCAP", stock_name="Ugro Capital Ltd",
                    exchange="NSE", sector="Fintech & MSME Lending", market_cap_tier="Small Cap",
                    weight_pct=8.0, current_price=245.0,
                    primary_reason="Data-tech driven MSME specialized lender utilizing GST, banking data, and bureau algorithms to underwrite loans in partnership with major public sector banks.",
                    competitive_moat="Co-lending architecture allowing Ugro to originate high-quality loans, earn origination fees, and keep 80% off-balance sheet with partner banks.",
                    growth_catalyst="Scaling Assets Under Management (AUM) toward ₹20,000 Cr with expanding return on equity (ROE > 18%).",
                    risk_factor="Macroeconomic shocks affecting informal Indian small businesses and MSME borrower repayment capacity.",
                    investor_label="Fintech MSME Co-Lending Alpha"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ROUTE", clean_symbol="ROUTE", stock_name="Route Mobile Ltd",
                    exchange="NSE", sector="Cloud Communications (CPaaS)", market_cap_tier="Small Cap",
                    weight_pct=7.0, current_price=1520.0,
                    primary_reason="Global Cloud Communications Platform as a Service (CPaaS) provider handling mission-critical OTPs, enterprise SMS, WhatsApp Business, and RCS messaging.",
                    competitive_moat="Direct telecom operator connectivity across 900+ mobile networks worldwide, delivering superior routing speeds and lower message drop rates.",
                    growth_catalyst="Acquisition by Belgian telecom giant Proximus Group creating global scale in enterprise omnichannel messaging.",
                    risk_factor="Telecom carrier wholesale SMS termination tariff hikes squeezing gross profit margins.",
                    investor_label="Digital Infrastructure SaaS Play"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SOMANYCERA", clean_symbol="SOMANYCERA", stock_name="Somany Ceramics Ltd",
                    exchange="NSE", sector="Ceramic Tiles & Sanitaryware", market_cap_tier="Small Cap",
                    weight_pct=5.5, current_price=640.0,
                    primary_reason="Legacy top-3 brand in ceramic tiles and bathware with comprehensive pan-India distribution and expanding export presence.",
                    competitive_moat="Established brand equity, state-of-the-art modern manufacturing plants, and strong institutional real estate developer relationships.",
                    growth_catalyst="Residential real estate completions and home renovation tailwinds in semi-urban India.",
                    risk_factor="Raw material fuel cost fluctuations and intense unorganized competition from Morbi tile clusters.",
                    investor_label="Consumer Home Building Play"
                ),
                TopPortfolioHolding(
                    symbol="NSE:HINDWAREAP", clean_symbol="HINDWAREAP", stock_name="Hindware Home Innovation Ltd",
                    exchange="NSE", sector="Consumer Sanitaryware & Kitchen Appliances", market_cap_tier="Small Cap",
                    weight_pct=5.5, current_price=340.0,
                    primary_reason="Pure-play consumer housing franchise controlling iconic 'Hindware' sanitaryware brand, kitchen chimneys, and consumer water heaters.",
                    competitive_moat="Deep multi-decade distribution network of 3,000+ dealers and high brand trust among architects and interior designers.",
                    growth_catalyst="Urban housing boom and formalization of premium kitchen and bathware fittings.",
                    risk_factor="Consumer durable demand slowdown and competitive discounting from multinational bathware entrants.",
                    investor_label="Consumer Home Improvement"
                ),
            ]
        )

    # =========================================================================
    # 8. BUFFETT & MUNGER INDIA HIGH-MOAT COMPOUNDERS
    # =========================================================================
    @classmethod
    def buffett_munger_india_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="buffett-munger-india",
            name="Buffett & Munger High-Moat India Compounders",
            manager_or_style="Quantitative High-Moat Model Portfolio",
            subtitle="Durable Competitive Advantage, Pricing Power & Multi-Decade Compounding",
            description="Institutional flagship portfolio embodying Warren Buffett and Charlie Munger principles adapted to the Indian economy: wide economic moats, pristine balance sheets, pricing power, negative working capital, and ROCE exceeding 25%.",
            category="Institutional Thematic",
            icon="🏰",
            dominant_philosophy="High Moat & Quality Compounding",
            risk_level="Conservative Quality",
            typical_holding_horizon="Multi-Decade Hold",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:TCS", clean_symbol="TCS", stock_name="Tata Consultancy Services Ltd",
                    exchange="NSE", sector="Information Technology & Digital Services", market_cap_tier="Large Cap",
                    weight_pct=16.0, current_price=4120.0,
                    primary_reason="India's corporate crown jewel. Unmatched global delivery execution, 35%+ ROCE, zero debt, and multi-billion-dollar enterprise transformation contracts.",
                    competitive_moat="High switching costs for global banks and Fortune 500 enterprises whose core infrastructure runs on TCS software; fortress brand trust.",
                    growth_catalyst="Global enterprise AI modernization, cloud migrations, and mega cost-efficiency outsourcing contracts.",
                    risk_factor="Prolonged discretionary tech budget freeze among North American banking and telecom clients.",
                    investor_label="Generational Quality Fortress"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ASIANPAINT", clean_symbol="ASIANPAINT", stock_name="Asian Paints Ltd",
                    exchange="NSE", sector="Decorative Paints & Home Decor", market_cap_tier="Large Cap",
                    weight_pct=13.0, current_price=2920.0,
                    primary_reason="The legendary supply-chain business school case study. Delivers tinting machines directly to 75,000+ retail dealers multiple times a day with negative working capital.",
                    competitive_moat="Unbeatable distribution density, dealer lock-in, unmatched customer brand recall, and massive purchasing scale in titanium dioxide and resins.",
                    growth_catalyst="Home painting frequency reduction (from 7 years to 3-4 years), waterproofing expansion, and home decor integration.",
                    risk_factor="Aggressive competitive entry by Aditya Birla Group's Birla Opus into decorative paints.",
                    investor_label="Supply-Chain Distribution Monopoly"
                ),
                TopPortfolioHolding(
                    symbol="NSE:HDFCBANK", clean_symbol="HDFCBANK", stock_name="HDFC Bank Ltd",
                    exchange="NSE", sector="Private Banking & Mortgage Powerhouse", market_cap_tier="Large Cap",
                    weight_pct=13.0, current_price=1740.0,
                    primary_reason="India's largest and most systemically important private lender. Unassailable low-cost CASA deposit franchise and conservative underwriting through all economic cycles.",
                    competitive_moat="Massive nationwide branch network of 8,500+ branches, technological scale, and complete cross-sell ownership of home mortgages, auto loans, and cards.",
                    growth_catalyst="Post-merger cross-selling of banking products to HDFC mortgage customers and gradual improvement in credit-deposit ratios.",
                    risk_factor="Near-term margin compression while absorbing high-cost wholesale HDFC parent borrowings.",
                    investor_label="Financial Sovereign Proxy"
                ),
                TopPortfolioHolding(
                    symbol="NSE:HINDUNILVR", clean_symbol="HINDUNILVR", stock_name="Hindustan Unilever Ltd",
                    exchange="NSE", sector="FMCG & Consumer Staples", market_cap_tier="Large Cap",
                    weight_pct=12.0, current_price=2680.0,
                    primary_reason="Reaches 9 out of 10 Indian households through 9 million retail outlets. Generates massive free cash flows with negative working capital and zero net debt.",
                    competitive_moat="Dozens of market-leading brands (Surf Excel, Dove, Lifebuoy, Red Label, Horlicks) with pricing power and vast rural distribution.",
                    growth_catalyst="Premiumization of personal care and rural FMCG volume recovery as farm incomes rise.",
                    risk_factor="Persistent rural wage slowdown and competition from nimble direct-to-consumer digital brands.",
                    investor_label="Everyday Essential Cash Machine"
                ),
                TopPortfolioHolding(
                    symbol="NSE:PIDILITIND", clean_symbol="PIDILITIND", stock_name="Pidilite Industries Ltd",
                    exchange="NSE", sector="Adhesives, Sealants & Construction Chemicals", market_cap_tier="Large Cap",
                    weight_pct=11.0, current_price=3180.0,
                    primary_reason="Monopolistic 70%+ market share in consumer adhesives (Fevicol, M-Seal, Dr. Fixit, Fevikwik). The brand name Fevicol is synonymous with adhesives.",
                    competitive_moat="Decades of deep emotional carpenter community engagement (Fevicol Champions Club), distributor loyalty, and product reliability.",
                    growth_catalyst="Construction chemicals, tile adhesives (Roff), and waterproofing adoption across urban real estate.",
                    risk_factor="Volatile raw material costs (Vinyl Acetate Monomer - VAM) tied to global oil prices.",
                    investor_label="Consumer Monopoly with Pricing Power"
                ),
                TopPortfolioHolding(
                    symbol="NSE:TITAN", clean_symbol="TITAN", stock_name="Titan Company Ltd",
                    exchange="NSE", sector="Branded Jewelry & Watches", market_cap_tier="Large Cap",
                    weight_pct=10.0, current_price=3480.0,
                    primary_reason="Tata brand credibility in hallmarked gold jewelry and lifestyle accessories compounding at 20%+ ROCE with structural retail market-share gains.",
                    competitive_moat="Consumer trust in gold purity, unmatched design collections (Tanishq, Mia, Zoya), and superior retail unit economics.",
                    growth_catalyst="Middle-class wedding consumer demand and formalization of the jewelry sector.",
                    risk_factor="Gold spot price volatility and custom import duty fluctuations.",
                    investor_label="Luxury Brand Compounding Moat"
                ),
                TopPortfolioHolding(
                    symbol="NSE:NESTLEIND", clean_symbol="NESTLEIND", stock_name="Nestle India Ltd",
                    exchange="NSE", sector="Packaged Foods & Nutrition", market_cap_tier="Large Cap",
                    weight_pct=8.0, current_price=2420.0,
                    primary_reason="Ultra-high ROCE (>100%) packaged food giant with iconic categories (Maggi noodles, KitKat, Nescafe, Cerelac) commanding exceptional brand loyalty.",
                    competitive_moat="Deep emotional resonance with generations of Indian consumers, proprietary recipes, and impenetrable shelf-space dominance.",
                    growth_catalyst="Expansion of rural distribution network and innovation in healthy culinary offerings.",
                    risk_factor="Commodity input cost spikes (wheat, palm oil, green coffee beans, milk).",
                    investor_label="Ultra-High Return on Capital"
                ),
                TopPortfolioHolding(
                    symbol="NSE:LT", clean_symbol="LT", stock_name="Larsen & Toubro Ltd",
                    exchange="NSE", sector="Engineering & Megaproject Infrastructure", market_cap_tier="Large Cap",
                    weight_pct=6.0, current_price=3640.0,
                    primary_reason="India's sole engineering company capable of building complex mega-projects (high-speed rail, nuclear power plants, deepwater platforms).",
                    competitive_moat="Insurmountable balance sheet size, sovereign trust, and proprietary engineering design workforce of over 50,000 engineers.",
                    growth_catalyst="Trillion-dollar infrastructure pipeline in India and massive Middle East green energy and hydrocarbon orders.",
                    risk_factor="Geopolitical tensions in the Middle East and delays in public project milestone approvals.",
                    investor_label="National Engineering Pillar"
                ),
                TopPortfolioHolding(
                    symbol="NSE:BAJFINANCE", clean_symbol="BAJFINANCE", stock_name="Bajaj Finance Ltd",
                    exchange="NSE", sector="Consumer Financing & Fintech", market_cap_tier="Large Cap",
                    weight_pct=6.0, current_price=7150.0,
                    primary_reason="India's most successful consumer lending franchise with proprietary point-of-sale customer acquisition engine and 85+ million customer franchise.",
                    competitive_moat="Zero-interest consumer durable financing partnerships with every major electronics retailer and proprietary risk algorithms.",
                    growth_catalyst="Scaling SME commercial financing, auto loans, and digital payments app cross-selling.",
                    risk_factor="Rising credit costs in unsecured personal loans and micro-finance portfolios.",
                    investor_label="Fintech-Scale Consumer Lending"
                ),
                TopPortfolioHolding(
                    symbol="NSE:KOTAKBANK", clean_symbol="KOTAKBANK", stock_name="Kotak Mahindra Bank Ltd",
                    exchange="NSE", sector="Private Banking & Wealth Management", market_cap_tier="Large Cap",
                    weight_pct=5.0, current_price=1780.0,
                    primary_reason="Fortress balance sheet with industry-leading capital adequacy (>20%), conservative risk culture, and market dominance in high-net-worth wealth management.",
                    competitive_moat="Premier private banking and investment banking arm (Kotak Securities & Kotak Capital) serving India's top corporate houses.",
                    growth_catalyst="Resolution of digital customer acquisition regulatory upgrades and expansion into commercial asset-backed lending.",
                    risk_factor="Intense competition for retail deposits across Indian private banking.",
                    investor_label="Fortress Balance Sheet Banking"
                ),
            ]
        )

    # =========================================================================
    # 9. INDIA INFRASTRUCTURE & DEFENSE CAPEX SUPERCYCLE
    # =========================================================================
    @classmethod
    def infra_defense_supercycle_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="infra-defense-supercycle",
            name="India Infrastructure & Defense Capex Supercycle",
            manager_or_style="Quantitative Thematic Macro Portfolio",
            subtitle="Trillion-Dollar Nation Building, Indigenization & Power Renaissance",
            description="Hand-crafted portfolio positioned to capture the multi-year supercycle in Indian government capital expenditure: indigenous defense manufacturing, high-speed rail, power grid modernization, and industrial automation.",
            category="Institutional Thematic",
            icon="🛡️",
            dominant_philosophy="Capex Supercycle & Indigenization",
            risk_level="Moderate Growth",
            typical_holding_horizon="3-5 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:LT", clean_symbol="LT", stock_name="Larsen & Toubro Ltd",
                    exchange="NSE", sector="Megaproject EPC & Defense Systems", market_cap_tier="Large Cap",
                    weight_pct=18.0, current_price=3640.0,
                    primary_reason="Indisputable anchor of Indian capex. Unrivaled order book exceeding ₹4,75,000 Cr across high-speed rail, ports, airports, green hydrogen, and naval defense.",
                    competitive_moat="Engineering mastery, massive credit rating, and sovereign execution credibility that global and Indian competitors cannot match.",
                    growth_catalyst="Domestic infrastructure capex push and multi-billion-dollar energy transition orders from Saudi Aramco and GCC nations.",
                    risk_factor="Geopolitical volatility in the Middle East impacting project timelines.",
                    investor_label="Anchor Infrastructure Heavyweight"
                ),
                TopPortfolioHolding(
                    symbol="NSE:BEL", clean_symbol="BEL", stock_name="Bharat Electronics Ltd",
                    exchange="NSE", sector="Defense Electronics & Radars", market_cap_tier="Large Cap",
                    weight_pct=15.0, current_price=290.0,
                    primary_reason="Navratna PSU monopoly supplying ~80% of all electronic warfare systems, air defense radars, communication suites, and avionics to Indian Armed Forces.",
                    competitive_moat="Sovereign technological alignment with DRDO and military forces, debt-free balance sheet, and massive order backlog (>₹75,000 Cr).",
                    growth_catalyst="Indigenous missile programs (Akash, QRSAM), fighter aircraft avionics, and non-defense electronic voting / railway signaling diversification.",
                    risk_factor="Dependence on central government defense budgetary allocations.",
                    investor_label="Defense Technology Monopoly"
                ),
                TopPortfolioHolding(
                    symbol="NSE:HAL", clean_symbol="HAL", stock_name="Hindustan Aeronautics Ltd",
                    exchange="NSE", sector="Aerospace & Defense Aviation", market_cap_tier="Large Cap",
                    weight_pct=14.0, current_price=4450.0,
                    primary_reason="Sole Indian manufacturer of military fighter jets (LCA Tejas), combat helicopters (Prachand, Dhruv), and aircraft jet engines; order book >₹1,20,000 Cr.",
                    competitive_moat="Monopoly in sovereign military aviation design, production, maintenance, and lifetime overhauls for the Indian Air Force and Navy.",
                    growth_catalyst="Cabinet approval for 97 additional Tejas Mark-1A fighter jets, GE-414 jet engine co-production, and helicopter export contracts.",
                    risk_factor="Engine delivery bottlenecks from global suppliers (GE Aerospace).",
                    investor_label="Sovereign Aerospace Giant"
                ),
                TopPortfolioHolding(
                    symbol="NSE:BHARATFORG", clean_symbol="BHARATFORG", stock_name="Bharat Forge Ltd",
                    exchange="NSE", sector="Heavy Forging & Defense Artillery", market_cap_tier="Large Cap",
                    weight_pct=11.0, current_price=1450.0,
                    primary_reason="Global forging leader successfully transformed into a premier defense hardware powerhouse, manufacturing indigenous advanced artillery guns (ATAGS) and armored vehicles.",
                    competitive_moat="World's largest forging facilities with automated press lines and cutting-edge metallurgical engineering.",
                    growth_catalyst="Export contracts for mounted gun artillery systems to international armies and aerospace engine components scaling.",
                    risk_factor="Cyclical slowdown in Class-8 North American commercial truck orders.",
                    investor_label="Precision Defense Transformation"
                ),
                TopPortfolioHolding(
                    symbol="NSE:TATAPOWER", clean_symbol="TATAPOWER", stock_name="Tata Power Co Ltd",
                    exchange="NSE", sector="Power Utilities & Renewable Infrastructure", market_cap_tier="Large Cap",
                    weight_pct=10.0, current_price=420.0,
                    primary_reason="Integrated power powerhouse delivering 24/7 baseload electricity while aggressively constructing India's largest clean-energy, EV charging, and solar manufacturing infrastructure.",
                    competitive_moat="Vertically integrated utility covering coal power plants, solar manufacturing (4.3 GW cell/module plant), smart transmission grids, and retail distribution discoms.",
                    growth_catalyst="Rooftop solar PM Surya Ghar scheme, utility-scale solar pipeline, and 100,000+ public EV charging stations.",
                    risk_factor="Regulatory delays in tariff revisions and volatile imported thermal coal prices.",
                    investor_label="Power Grid & Transition Anchor"
                ),
                TopPortfolioHolding(
                    symbol="NSE:CUMMINSIND", clean_symbol="CUMMINSIND", stock_name="Cummins India Ltd",
                    exchange="NSE", sector="Power Generation & Diesel Engines", market_cap_tier="Large Cap",
                    weight_pct=8.0, current_price=3680.0,
                    primary_reason="Leading manufacturer of high-horsepower backup diesel generator sets for data centers, commercial hospitals, and industrial power infrastructure.",
                    competitive_moat="Market share exceeding 60% in heavy-duty backup power generators and rapid readiness for CPCB-IV+ emission compliance.",
                    growth_catalyst="Explosive Indian data center construction boom requiring mission-critical continuous backup power.",
                    risk_factor="Global parent sourcing policy shifts and raw material steel/copper inflation.",
                    investor_label="Data Center Power Beneficiary"
                ),
                TopPortfolioHolding(
                    symbol="NSE:NTPC", clean_symbol="NTPC", stock_name="NTPC Limited",
                    exchange="NSE", sector="Power Generation Utility", market_cap_tier="Large Cap",
                    weight_pct=7.0, current_price=410.0,
                    primary_reason="Generates ~25% of India's total electricity. Provides the indispensable thermal baseload required to power national industrial expansion while building 60 GW of renewables.",
                    competitive_moat="Regulated return-on-equity model guarantees stable 15.5% ROE on capital invested, with captive coal mines insulating fuel security.",
                    growth_catalyst="Listing of green energy subsidiary (NTPC Green Energy) and massive nuclear power joint ventures.",
                    risk_factor="High capital intensity and carbon transition policy risks.",
                    investor_label="Regulated Utility Cash Cow"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SIEMENS", clean_symbol="SIEMENS", stock_name="Siemens Ltd",
                    exchange="NSE", sector="Factory Automation & Smart Grids", market_cap_tier="Large Cap",
                    weight_pct=6.0, current_price=7450.0,
                    primary_reason="Global technological pioneer in smart electrical transmission, digital factory automation, and locomotive electric propulsion.",
                    competitive_moat="German engineering dominance in high-voltage switchgear, factory robotics, and Indian Railways' 9,000 HP electric locomotives.",
                    growth_catalyst="Demerger of energy business unlocking pure-play industrial automation and Indian grid modernization capex.",
                    risk_factor="Parent royalty payment disputes and high valuation multiples.",
                    investor_label="Smart Grid & Automation Leader"
                ),
                TopPortfolioHolding(
                    symbol="NSE:ABB", clean_symbol="ABB", stock_name="ABB India Ltd",
                    exchange="NSE", sector="Robotics, Electrification & Motion", market_cap_tier="Large Cap",
                    weight_pct=6.0, current_price=7850.0,
                    primary_reason="Leader in high-efficiency electric motors, industrial robotics, variable speed drives, and electrification infrastructure for data centers and metros.",
                    competitive_moat="Zero net debt, high return on capital, and proprietary energy-efficient motor technology reducing customer factory electricity costs by 20%.",
                    growth_catalyst="Government mandates for industrial energy efficiency, automation of manufacturing lines, and data center electrification.",
                    risk_factor="Expensive price-to-earnings multiples demanding uninterrupted double-digit margin growth.",
                    investor_label="High-Tech Electrification Play"
                ),
                TopPortfolioHolding(
                    symbol="NSE:RVNL", clean_symbol="RVNL", stock_name="Rail Vikas Nigam Ltd",
                    exchange="NSE", sector="Railway Infrastructure EPC", market_cap_tier="Mid Cap",
                    weight_pct=5.0, current_price=470.0,
                    primary_reason="Dedicated execution arm of the Ministry of Railways executing high-speed rail lines, major railway bridge construction, and metro rail networks.",
                    competitive_moat="Fast-track project allocation from Indian Railways and turnkey execution capability across difficult terrains.",
                    growth_catalyst="Vande Bharat sleeper train manufacturing consortium and international railway construction contracts in Central Asia and Maldives.",
                    risk_factor="Government procurement policy shifts and low operating margin profile typical of public EPC contracts.",
                    investor_label="Railway Modernization Play"
                ),
            ]
        )

    # =========================================================================
    # 10. GREEN ENERGY, EV & ENERGY TRANSITION
    # =========================================================================
    @classmethod
    def green_energy_ev_transition_portfolio(cls) -> TopMarketPortfolio:
        return TopMarketPortfolio(
            id="green-energy-ev-transition",
            name="Green Energy, EV & Clean-Tech Transition",
            manager_or_style="Quantitative Clean-Tech Thematic Portfolio",
            subtitle="Secular Decarbonization, Electric Mobility & Energy Storage",
            description="Focused on India's secular multi-decade clean-energy transition toward Net-Zero 2070: domestic solar manufacturing, wind repowering, EV battery gigafactories, and smart distribution corridors.",
            category="Institutional Thematic",
            icon="🌱",
            dominant_philosophy="Clean Energy & Electric Mobility",
            risk_level="Aggressive Growth",
            typical_holding_horizon="5-10 Years",
            holdings=[
                TopPortfolioHolding(
                    symbol="NSE:TATAPOWER", clean_symbol="TATAPOWER", stock_name="Tata Power Co Ltd",
                    exchange="NSE", sector="Integrated Clean Energy & Solar", market_cap_tier="Large Cap",
                    weight_pct=18.0, current_price=420.0,
                    primary_reason="Pivotal clean energy champion in India with fully commissioned 4.3 GW solar cell and module plant in Tirunelveli and 100,000+ public EV charging points.",
                    competitive_moat="Complete vertical integration across renewable generation, in-house solar cell manufacturing, rooftop solar distribution, and smart city discoms.",
                    growth_catalyst="PM Surya Ghar Muft Bijli Yojana rooftop solar residential installation boom and utility solar pipelines.",
                    risk_factor="State electricity discom payment delays and regulatory tariff approval cycles.",
                    investor_label="Anchor Clean-Energy Champion"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SUZLON", clean_symbol="SUZLON", stock_name="Suzlon Energy Ltd",
                    exchange="NSE", sector="Wind Turbines & Renewable EPC", market_cap_tier="Mid Cap",
                    weight_pct=14.0, current_price=68.0,
                    primary_reason="Spectacular debt-free turnaround commanding ~32% market share in Indian wind turbine generation with record-high 3.8+ GW order book.",
                    competitive_moat="Proprietary 3 MW+ wind turbine technology optimized for India's low-wind regimes, supported by lifetime operations and maintenance (O&M) annuity cash flows.",
                    growth_catalyst="Commercial and industrial (C&I) green power purchase agreements and hybrid wind-solar tenders by SECI.",
                    risk_factor="Right-of-way land acquisition challenges and grid evacuation substation availability in windy states (Gujarat, Tamil Nadu).",
                    investor_label="Wind Energy Turnaround Champion"
                ),
                TopPortfolioHolding(
                    symbol="NSE:OLECTRA", clean_symbol="OLECTRA", stock_name="Olectra Greentech Ltd",
                    exchange="NSE", sector="Electric Buses & Commercial Heavy EV", market_cap_tier="Small Cap",
                    weight_pct=12.0, current_price=1680.0,
                    primary_reason="First-mover pioneer in electric buses in India; partnership with global EV battery leader BYD with a massive order book exceeding 10,000 e-buses.",
                    competitive_moat="Commercial electric bus homologation approvals across major state transport undertakings (BEST Mumbai, TSRTC, DTC Delhi).",
                    growth_catalyst="Commissioning of new Greenfield mega-factory in Hyderabad (10,000 units capacity) and expansion into electric tipper trucks.",
                    risk_factor="State transport corporation payment schedules and reliance on BYD battery technology.",
                    investor_label="Electric Public Mobility Pioneer"
                ),
                TopPortfolioHolding(
                    symbol="NSE:EXIDEIND", clean_symbol="EXIDEIND", stock_name="Exide Industries Ltd",
                    exchange="NSE", sector="Advanced Battery Storage & EV Cells", market_cap_tier="Mid Cap",
                    weight_pct=11.0, current_price=480.0,
                    primary_reason="Legacy lead-acid battery titan constructing India's largest dedicated lithium-ion gigafactory in Bengaluru, backed by technological partner SVOLT.",
                    competitive_moat="Unbeatable nationwide dealer network of 50,000+ points and long-term supply agreements with Hyundai, Kia, and commercial EV fleets.",
                    growth_catalyst="Commercial production of multi-gigawatt lithium-ion battery cells for EVs and grid-scale energy storage systems.",
                    risk_factor="Execution risk in commercial gigafactory ramp-up and raw lithium price volatility.",
                    investor_label="Battery Gigafactory Transition"
                ),
                TopPortfolioHolding(
                    symbol="NSE:SWOLAR", clean_symbol="SWOLAR", stock_name="Sterling and Wilson Renewable Energy",
                    exchange="NSE", sector="Utility-Scale Solar EPC", market_cap_tier="Small Cap",
                    weight_pct=10.0, current_price=530.0,
                    primary_reason="Reliance Industries and Shapoorji Pallonji backed global solar EPC contractor executing giga-scale utility solar installations across India, Middle East, and Australia.",
                    competitive_moat="Over 15 GW of commissioned solar project track record globally and preferential access to Reliance's upcoming new energy ecosystem.",
                    growth_catalyst="Execution of massive NTPC Khavda ultra-mega solar project and international utility-scale solar order additions.",
                    risk_factor="Legacy project indemnity settlement liabilities and fixed-price module cost inflation.",
                    investor_label="Utility Solar EPC Scale"
                ),
                TopPortfolioHolding(
                    symbol="NSE:TMCV", clean_symbol="TMCV", stock_name="Tata Motors Commercial Vehicles Ltd",
                    exchange="NSE", sector="Electric Passenger Cars & Fleet", market_cap_tier="Large Cap",
                    weight_pct=9.0, current_price=960.0,
                    primary_reason="Dominant leader (>70% market share) in Indian electric passenger vehicles with best-selling models (Nexon.ev, Punch.ev, Tiago.ev).",
                    competitive_moat="Ecosystem advantage through Tata Power charging infrastructure and group battery manufacturing, creating massive barriers for rivals.",
                    growth_catalyst="Launch of dedicated pure EV skateboard architecture models (Curvv.ev, Harrier.ev, Avinya) and rising EV adoption in metros.",
                    risk_factor="Aggressive EV model launches by Mahindra and Hyundai targeting the mass consumer bracket.",
                    investor_label="Electric Passenger Mobility Leader"
                ),
                TopPortfolioHolding(
                    symbol="NSE:JSWENERGY", clean_symbol="JSWENERGY", stock_name="JSW Energy Ltd",
                    exchange="NSE", sector="Renewable Power & Energy Storage", market_cap_tier="Large Cap",
                    weight_pct=8.0, current_price=690.0,
                    primary_reason="Rapidly scaling clean power platform targeting 20 GW of power capacity by 2030, coupled with major battery energy storage systems (BESS).",
                    competitive_moat="Strong balance sheet backing from JSW Group, captive industrial power demand from JSW Steel, and high operational plant availability.",
                    growth_catalyst="Commissioning of multi-gigawatt wind/solar assets and commercial operations of SECI-contracted battery storage.",
                    risk_factor="Execution lead times on large renewable grid connectivity projects.",
                    investor_label="Clean Energy Scaling Powerhouse"
                ),
                TopPortfolioHolding(
                    symbol="NSE:KPIGREEN", clean_symbol="KPIGREEN", stock_name="KPI Green Energy Ltd",
                    exchange="NSE", sector="Solar & Wind Hybrid Power IPP", market_cap_tier="Small Cap",
                    weight_pct=7.0, current_price=760.0,
                    primary_reason="Fast-growing solar and hybrid power producer in Gujarat providing green energy directly to commercial and industrial (C&I) corporate clients.",
                    competitive_moat="Captive power transmission infrastructure in Gujarat industrial clusters enabling high-tariff corporate power purchase agreements.",
                    growth_catalyst="Aggressive target of achieving 1 GW operational renewable capacity and expanding into multi-state corporate PPA markets.",
                    risk_factor="Concentration of power assets in Gujarat and reliance on capital debt for new solar park development.",
                    investor_label="High-Growth Corporate Green PPA"
                ),
                TopPortfolioHolding(
                    symbol="NSE:WAAREE", clean_symbol="WAAREE", stock_name="Waaree Energies Ltd",
                    exchange="NSE", sector="Solar Module Manufacturing", market_cap_tier="Large Cap",
                    weight_pct=6.0, current_price=2850.0,
                    primary_reason="India's largest solar photovoltaic module manufacturer with 13+ GW operational capacity and substantial exports to the United States.",
                    competitive_moat="Largest manufacturing scale in India, government approved ALMM (Approved List of Module Manufacturers) listing, and backward integration into solar cells.",
                    growth_catalyst="Protection from cheap Chinese solar panel dumping via domestic content requirements (DCR) and US export demand.",
                    risk_factor="Policy shifts in US solar import tariffs and domestic polysilicon price swings.",
                    investor_label="Solar PV Manufacturing Leader"
                ),
                TopPortfolioHolding(
                    symbol="NSE:BORORENEW", clean_symbol="BORORENEW", stock_name="Borosil Renewables Ltd",
                    exchange="NSE", sector="Low-Iron Solar Glass", market_cap_tier="Small Cap",
                    weight_pct=5.0, current_price=510.0,
                    primary_reason="Sole Indian manufacturer of solar tempered glass used in photovoltaic panels, protected by anti-dumping duties on Chinese and Vietnamese imports.",
                    competitive_moat="Complex glass furnace technology requiring continuous 24/7 manufacturing operations and long technical qualifications with solar module makers.",
                    growth_catalyst="Rapid capacity expansions from 450 TPD to 1,000+ TPD feeding India's domestic solar module manufacturing boom.",
                    risk_factor="Fluctuations in soda ash and natural gas energy costs, and intermittent Chinese solar glass dumping.",
                    investor_label="Solar Component Monopoly Asset"
                ),
            ]
        )
