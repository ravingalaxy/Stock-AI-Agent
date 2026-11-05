"""
Streamlit Web Dashboard for AI Stock Research & Ranking Agent.
Features the flagship "Portfolio Analysis and Expert-Style Evaluation" module.
Supports CSV, XLSX, XLS, PDF, and DOCX broker holding statements.
"""

import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.portfolio.portfolio_parser import PortfolioParser, ParsedPortfolio
from src.portfolio.portfolio_analyzer import PortfolioAnalyzer, PortfolioMetrics
from src.portfolio.investor_styles import PortfolioInvestorStyles, PortfolioStyleProfile
from src.portfolio.portfolio_report import PortfolioReportGenerator, ExpertPortfolioReview, COMPLIANCE_DISCLAIMER
from src.portfolio.top_portfolios import TopPortfoliosRepository, TopMarketPortfolio

st.set_page_config(
    page_title="AI Stock Research Agent - Portfolio Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric {
        background: #151d30;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def render_portfolio_analysis_tab():
    """Main Portfolio Analysis and Expert-Style Evaluation View."""
    st.title("📊 Portfolio Analysis & Expert-Style Evaluation")
    st.caption("Universal statement ingestion (CSV, XLSX, XLS, PDF, DOCX), 9 Legendary Investor scoring, concentration risk, and senior expert review.")

    # Compliance Disclaimer Banner
    st.warning(f"⚖️ **COMPLIANCE DISCLAIMER:** {COMPLIANCE_DISCLAIMER}")

    # File Uploader
    st.subheader("📁 Upload Broker Holdings Statement")

    # Session state management for reset functionality
    if "portfolio_uploader_key" not in st.session_state:
        st.session_state["portfolio_uploader_key"] = 0
    if "load_sample" not in st.session_state:
        st.session_state["load_sample"] = True

    col_upload, col_sample, col_reset = st.columns([3, 1.2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Select holding statement file",
            type=["csv", "xlsx", "xls", "pdf", "docx"],
            key=f"portfolio_file_{st.session_state['portfolio_uploader_key']}",
            help="Supports FYERS, Zerodha, Upstox, Groww, Angel One, ICICI Direct, and standard broker statements."
        )

    with col_sample:
        st.write("")
        st.write("")
        sample_path = BASE_DIR / "sample_portfolio_statement.csv"
        if not sample_path.exists():
            sample_path = BASE_DIR / "FYERS_holding_statements_XR45621_2026-10-23.csv"
        default_sample_val = st.session_state["load_sample"] and (uploaded_file is None and sample_path.exists())
        use_sample = st.checkbox("Load Sample Statement", value=default_sample_val, key=f"chk_sample_{st.session_state['portfolio_uploader_key']}")

    with col_reset:
        st.write("")
        st.write("")
        if st.button("🔄 Reset", help="Reset and clear statement upload", use_container_width=True):
            st.session_state["portfolio_uploader_key"] += 1
            st.session_state["load_sample"] = False
            st.rerun()

    parsed = None
    if uploaded_file is not None:
        try:
            content = uploaded_file.read()
            parsed = PortfolioParser.parse_file(content, filename=uploaded_file.name)
            if not parsed.is_valid:
                st.error("Failed to parse statement: " + "; ".join(parsed.errors))
                return
            st.success(f"Successfully parsed '{uploaded_file.name}' ({len(parsed.holdings)} holdings detected)")
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")
            return
    elif use_sample and sample_path.exists():
        parsed = PortfolioParser.parse_file(sample_path)

    if not parsed or not parsed.is_valid:
        st.info("ℹ️ No portfolio loaded. Upload a broker statement (CSV, XLSX, XLS, PDF, DOCX) above, or click 'Load FYERS Sample' to explore.")
        if st.button("🔄 Load Sample Portfolio"):
            st.session_state["load_sample"] = True
            st.rerun()
        return

    # Run Analysis
    metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
    style_profile = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)
    review = ExpertPortfolioReview(metrics, style_profile).generate_review()

    # Statement Metadata Banner
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.7); padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-family: monospace; font-size: 0.85rem; color: #94a3b8; display: flex; justify-content: space-between; flex-wrap: wrap;">
        <span><strong>Statement Date:</strong> {metrics.statement_date}</span>
        <span><strong>Client ID:</strong> {metrics.client_id}</span>
        <span><strong>Client Name:</strong> {metrics.client_name}</span>
        <span><strong>File:</strong> {parsed.filename}</span>
    </div>
    """, unsafe_allow_html=True)

    # 1. Summary Cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Invested", f"₹{metrics.total_invested:,.0f}")
    with col2:
        st.metric("Current Value", f"₹{metrics.total_current:,.0f}")
    with col3:
        pnl_delta = f"{metrics.total_pnl_pct:+.2f}%"
        st.metric("Net Unrealized P&L", f"₹{metrics.total_pnl:+,.0f}", delta=pnl_delta)
    with col4:
        st.metric("Quality Score", f"{metrics.portfolio_quality_score:.1f}/100")
    with col5:
        st.metric("Diversification", f"{metrics.portfolio_diversification_score:.1f}/100")
    with col6:
        st.metric("Portfolio Risk", f"{metrics.portfolio_risk_score:.1f}/100", delta_color="inverse")

    st.markdown("---")

    # 2. Charts Row: Sector Allocation & Stock Weights & Market Cap
    st.subheader("📈 Asset Allocation & Exposure Analytics")
    tab_sector, tab_weights, tab_mcap = st.tabs(["Sector Allocation", "Stock Weights", "Market-Cap Tiers"])

    with tab_sector:
        df_sec = pd.DataFrame([
            {"Sector": sec, "Weight (%)": d["weight_pct"], "Current Value (₹)": d["value"], "Holdings Count": len(d["stocks"])}
            for sec, d in metrics.sector_allocation.items()
        ]).sort_values(by="Weight (%)", ascending=False)
        fig_sec = px.pie(
            df_sec, names="Sector", values="Current Value (₹)",
            title="Portfolio Allocation by Sector",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig_sec.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_sec, use_container_width=True)
        st.dataframe(df_sec, use_container_width=True, hide_index=True)

    with tab_weights:
        top_stocks = metrics.holdings_analysis[:12]
        df_weights = pd.DataFrame([
            {"Rank": i + 1, "Symbol": h.clean_symbol, "Name": h.stock_name, "Quantity": int(h.quantity), "Weight (%)": h.weight_pct, "Value (₹)": round(h.current_value, 2), "P&L (%)": round(h.pnl_pct, 2)}
            for i, h in enumerate(top_stocks)
        ])
        fig_weights = px.bar(
            df_weights, x="Weight (%)", y="Symbol", orientation="h",
            title="Top 12 Holdings by Portfolio Weight (%)",
            color="Weight (%)",
            color_continuous_scale="Viridis"
        )
        fig_weights.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_weights, use_container_width=True)
        st.dataframe(df_weights, use_container_width=True, hide_index=True)

    with tab_mcap:
        df_mcap = pd.DataFrame([
            {"Market Cap Tier": tier, "Weight (%)": d["weight_pct"], "Current Value (₹)": d["value"], "Stocks Count": len(d["stocks"])}
            for tier, d in metrics.market_cap_allocation.items()
        ]).sort_values(by="Weight (%)", ascending=False)
        fig_mcap = px.bar(
            df_mcap, x="Market Cap Tier", y="Weight (%)",
            title="Market-Cap Allocation (% of Total Portfolio)",
            color="Market Cap Tier",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_mcap, use_container_width=True)
        st.dataframe(df_mcap, use_container_width=True, hide_index=True)

    # 3. Best vs Worst Performers
    st.subheader("⚡ Performance Drivers & Drawdown Analysis")
    col_best, col_worst = st.columns(2)
    with col_best:
        st.markdown("##### 🚀 Top Performers (Alpha Contributors)")
        for b in metrics.best_performers:
            st.success(f"**{b['symbol']}**: +{b['pnl_pct']:.1f}% (+₹{b['pnl_amount']:,.0f}) | {b['name']} ({b['weight_pct']:.1f}% wt)")
    with col_worst:
        st.markdown("##### 🔻 Lagging Holdings (Capital Drag)")
        for w in metrics.worst_performers:
            st.error(f"**{w['symbol']}**: {w['pnl_pct']:.1f}% (₹{w['pnl_amount']:,.0f}) | {w['name']} ({w['weight_pct']:.1f}% wt)")

    # 4. Concentration & Risk Alerts
    st.subheader("🛡️ Concentration & Overlap Guardrails")
    col_conc, col_grp = st.columns(2)
    with col_conc:
        st.markdown("##### 🚨 Single-Stock / Sector Concentration")
        if metrics.excessive_concentration_stocks:
            for alert in metrics.excessive_concentration_stocks:
                st.warning(f"**{alert['name']}** ({alert['weight_pct']:.1f}%): {alert['reason']}")
        else:
            st.info("✅ All individual stock weights are within the 15% prudential ceiling.")

    with col_grp:
        st.markdown("##### 🔗 Corporate Groups & Duplicate Exposures")
        if metrics.overlapping_exposures:
            for grp in metrics.overlapping_exposures:
                st.info(f"**{grp['group_name']}** ({grp['combined_weight_pct']:.1f}% Combined): {grp['insight']}")
        else:
            st.info("✅ No redundant ETF allocations or group cluster concentrations detected.")

    # 5. 9 Legendary Investor Scorecard
    st.subheader("🏛️ 9 Legendary Investor Style Scorecard")
    st.info(f"**Dominant Strategy Fit:** `{style_profile.best_matching_investor}` (Score: {style_profile.top_score:.1f}/100) — *{style_profile.dominant_style}*")

    df_styles = pd.DataFrame([
        {
            "Strategy": row["strategy"],
            "Score (/100)": f"{row['score']:.1f}",
            "Verdict": "Strong Fit" if row["score"] >= 70 else "Moderate Fit" if row["score"] >= 50 else "Weak Fit",
            "Aligned Holdings": row["aligned_stocks"]
        }
        for row in style_profile.strategy_rows
    ])
    st.dataframe(df_styles, use_container_width=True, hide_index=True)

    # 6. Complete Holdings Matrix
    st.subheader("📋 Complete Portfolio Holdings Matrix")
    df_holdings = pd.DataFrame([
        {
            "Symbol": h.clean_symbol,
            "Company Name": h.stock_name,
            "Sector": h.sector,
            "Cap Tier": h.market_cap_tier,
            "Qty": int(h.quantity),
            "Buy Price (₹)": f"{h.buy_price:.2f}",
            "Current Price (₹)": f"{h.current_price:.2f}",
            "Current Value (₹)": f"{h.current_value:,.2f}",
            "Weight (%)": f"{h.weight_pct:.2f}%",
            "P&L (₹)": f"{h.pnl_amount:+,.2f}",
            "P&L (%)": f"{h.pnl_pct:+.2f}%",
            "Sizing": h.sizing_status,
            "Score": f"{h.stock_score:.1f}",
            "ISIN": h.isin
        }
        for h in metrics.holdings_analysis
    ])
    st.dataframe(df_holdings, use_container_width=True, hide_index=True)

    # 7. Senior Portfolio Review Analyst Breakdown
    st.subheader("🎓 Senior Portfolio Review & Expert Forensics")

    with st.expander("1. Executive Summary", expanded=True):
        st.write(review["portfolio_summary"])

    with st.expander("2. Demonstrated Portfolio Strengths", expanded=True):
        for s in review["strengths"]:
            st.markdown(f"- ✅ {s}")

    with st.expander("3. Weaknesses & Friction Points", expanded=True):
        for w in review["weaknesses"]:
            st.markdown(f"- ⚠️ {w}")

    with st.expander("4. Key Governance & Risk Flags", expanded=True):
        for rf in review["risk_flags"]:
            st.markdown(f"**{rf['category']}:** {', '.join(rf['items'])} — *{rf['assessment']}*")

    with st.expander("5. Strategic Questions for the Investor", expanded=False):
        for q in review["questions_for_investor"]:
            st.markdown(f"- ❓ {q}")

    with st.expander("6. Monitoring Checklist for Key Holdings", expanded=False):
        df_mon = pd.DataFrame(review["monitoring_checklist"])
        st.dataframe(df_mon, use_container_width=True, hide_index=True)

    # 8. Report Export Buttons
    st.subheader("💾 Export Portfolio Research Report")
    c_md, c_csv, c_xlsx, c_pdf = st.columns(4)

    with c_md:
        md_data = PortfolioReportGenerator.generate_markdown(metrics, style_profile)
        st.download_button(
            label="📄 Download Markdown (.md)",
            data=md_data,
            file_name=f"Portfolio_Report_{Path(parsed.filename).stem}.md",
            mime="text/markdown"
        )

    with c_csv:
        csv_data = PortfolioReportGenerator.generate_csv(metrics)
        st.download_button(
            label="📋 Download CSV (.csv)",
            data=csv_data,
            file_name=f"Portfolio_Holdings_{Path(parsed.filename).stem}.csv",
            mime="text/csv"
        )

    with c_xlsx:
        xlsx_data = PortfolioReportGenerator.generate_excel(metrics, style_profile)
        st.download_button(
            label="📊 Download Excel (.xlsx)",
            data=xlsx_data,
            file_name=f"Portfolio_Analysis_{Path(parsed.filename).stem}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with c_pdf:
        pdf_data = PortfolioReportGenerator.generate_pdf(metrics, style_profile)
        st.download_button(
            label="📕 Download PDF (.pdf)",
            data=pdf_data,
            file_name=f"Portfolio_Report_{Path(parsed.filename).stem}.pdf",
            mime="application/pdf"
        )


def render_top_portfolios_tab():
    """Top 10 Portfolios of Stock Market with exhaustive stock-by-stock rationales."""
    st.title("🏆 Top 10 Portfolios of Stock Market")
    st.caption("Dalal Street's Legendary Superinvestors & Premier Thematic Model Portfolios with In-Depth Investment Rationales.")

    st.warning(f"⚖️ **COMPLIANCE DISCLAIMER:** {COMPLIANCE_DISCLAIMER}")

    all_ports = TopPortfoliosRepository.get_all_portfolios()
    port_dict = {f"{p.icon} {p.name}": p for p in all_ports}

    # Search Bar
    search_q = st.text_input("🔍 Search any stock across all Top 10 Portfolios (e.g. TITAN, TATAPOWER, LT, DMART, IDEA):")
    if search_q.strip():
        results = TopPortfoliosRepository.find_stock_across_portfolios(search_q.strip())
        if results:
            st.success(f"Found {len(results)} occurrence(s) for '{search_q}':")
            for r in results:
                h = r["holding"]
                with st.expander(f"{h.clean_symbol} in {r['portfolio_name']} ({h.weight_pct}% Weight)"):
                    st.write(f"**Company:** {h.stock_name} | **Sector:** {h.sector} | **Role:** {h.investor_label}")
                    st.info(f"**🎯 Why Taken:** {h.primary_reason}")
                    st.write(f"**🏰 Moat:** {h.competitive_moat}")
                    st.write(f"**🚀 Catalyst:** {h.growth_catalyst}")
                    st.write(f"**⚠️ Key Risk:** {h.risk_factor}")
        else:
            clean_sq = search_q.strip().upper().replace(".NS", "").replace(".BO", "")
            from src.portfolio.portfolio_analyzer import INDIAN_EQUITY_METADATA
            if clean_sq in INDIAN_EQUITY_METADATA:
                meta = INDIAN_EQUITY_METADATA[clean_sq]
                st.info(f"ℹ️ **{meta['name']} ({clean_sq})** is an actively traded listed stock on NSE/BSE ({meta['sector']}), but is not currently held in Dalal Street's Top 10 Superinvestor Portfolios.")
            else:
                st.info(f"No holdings found matching '{search_q}' in Top 10 Portfolios.")

    st.markdown("---")

    # Portfolio Selector
    selected_name = st.selectbox("Select Portfolio to Explore:", list(port_dict.keys()))
    portfolio = port_dict[selected_name]

    # Executive Overview
    st.subheader(f"{portfolio.icon} {portfolio.name}")
    st.write(f"*{portfolio.subtitle}*")
    st.write(portfolio.description)

    # Summary KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Holdings Count", f"{portfolio.stock_count} Stocks")
    with col2:
        top_h = portfolio.top_holding
        st.metric("Top Holding", f"{top_h.clean_symbol} ({top_h.weight_pct}%)" if top_h else "N/A")
    with col3:
        st.metric("Risk Profile", portfolio.risk_level)
    with col4:
        st.metric("Holding Horizon", portfolio.typical_holding_horizon)

    st.markdown("---")

    # Charts Row: Sector Allocation & Market Cap
    c_sec, c_mcap = st.columns(2)
    with c_sec:
        st.markdown("##### 🥧 Sector Allocation")
        df_sec = pd.DataFrame([
            {"Sector": s, "Weight (%)": w} for s, w in portfolio.sector_allocation.items()
        ])
        fig_sec = px.pie(df_sec, names="Sector", values="Weight (%)", hole=0.4)
        st.plotly_chart(fig_sec, use_container_width=True)

    with c_mcap:
        st.markdown("##### 🏛️ Market-Cap Allocation")
        df_mcap = pd.DataFrame([
            {"Tier": t, "Weight (%)": w} for t, w in portfolio.market_cap_allocation.items()
        ])
        fig_mcap = px.bar(df_mcap, x="Tier", y="Weight (%)", color="Tier")
        st.plotly_chart(fig_mcap, use_container_width=True)

    st.markdown("---")

    # Complete Holdings & In-Depth Stock Rationales
    st.subheader(f"📋 Complete Holdings & Investment Rationales ({portfolio.stock_count} Stocks)")

    for h in portfolio.holdings:
        with st.expander(f"📌 {h.clean_symbol} — {h.stock_name} | {h.weight_pct}% Weight | {h.sector}", expanded=True):
            r1, r2 = st.columns(2)
            with r1:
                st.markdown(f"**🎯 Why This Stock Was Taken:**\n\n{h.primary_reason}")
                st.markdown(f"**🏰 Competitive Moat & Durability:**\n\n{h.competitive_moat}")
            with r2:
                st.markdown(f"**🚀 Primary Alpha Catalysts:**\n\n{h.growth_catalyst}")
                st.markdown(f"**⚠️ Key Surveillance & Risk:**\n\n{h.risk_factor}")
            st.caption(f"Category: {h.market_cap_tier} | Strategic Role: {h.investor_label} | Exchange: {h.exchange}")


def main():
    st.sidebar.title("AI Stock Research Agent")
    st.sidebar.caption("NSE & BSE Quantitative Intelligence Platform")

    tab_choice = st.sidebar.radio(
        "Navigation",
        ["📊 Portfolio Analysis", "🏆 Top 10 Portfolios", "📈 Market Dashboard & Tools"]
    )

    if tab_choice == "📊 Portfolio Analysis":
        render_portfolio_analysis_tab()
    elif tab_choice == "🏆 Top 10 Portfolios":
        render_top_portfolios_tab()
    else:
        st.info("To explore the full institutional Django Web Platform with real-time exchange tickers, visit http://127.0.0.1:8000/")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset Portfolio Analysis", use_container_width=True, help="Reset upload and reload default sample portfolio"):
        st.session_state["portfolio_uploader_key"] = st.session_state.get("portfolio_uploader_key", 0) + 1
        st.session_state["load_sample"] = True
        st.rerun()


if __name__ == "__main__":
    main()
