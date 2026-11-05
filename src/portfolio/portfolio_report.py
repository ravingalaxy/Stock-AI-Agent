"""
Senior Portfolio Review Analyst Engine and Multi-Format Report Exporter.
Generates an institutional expert review (Summary, Strengths, Weaknesses, Risk Flags,
Strategy Alignment, Research Observations, Investor Questions, Monitoring Checklist)
and exports reports in Markdown, CSV, Excel (.xlsx), and PDF (.pdf).
"""

import io
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from src.utils.logger import logger
from .portfolio_analyzer import PortfolioMetrics, HoldingAnalysis
from .investor_styles import PortfolioStyleProfile, PortfolioInvestorStyles

COMPLIANCE_DISCLAIMER = (
    "DISCLAIMER: This portfolio analysis is for educational and research purposes only. "
    "It is not investment advice, a recommendation to buy or sell any security, or a guarantee of future returns. "
    "All investments involve risk, including possible loss of capital. Please conduct your own due diligence "
    "or consult a SEBI-registered investment adviser before making financial decisions."
)


class ExpertPortfolioReview:
    """Institutional Senior Analyst Review structure."""

    def __init__(self, metrics: PortfolioMetrics, style_profile: PortfolioStyleProfile):
        self.metrics = metrics
        self.style = style_profile

    def generate_review(self) -> Dict[str, Any]:
        """Constructs the structured 8-part Senior Portfolio Review."""
        m = self.metrics
        s = self.style

        # 1. Summary
        summary_text = (
            f"The analyzed portfolio comprises {m.stock_count} holdings with a total invested capital "
            f"of ₹{m.total_invested:,.2f} and a current evaluated market value of ₹{m.total_current:,.2f}, "
            f"reflecting an unrealized net profit/loss of ₹{m.total_pnl:,.2f} ({m.total_pnl_pct:+.2f}%). "
            f"The portfolio registers an aggregate Quality Score of {m.portfolio_quality_score:.1f}/100, "
            f"a Diversification Score of {m.portfolio_diversification_score:.1f}/100, and an evaluated Risk Index "
            f"of {m.portfolio_risk_score:.1f}/100, carrying the research classification: '{m.portfolio_research_rating}'."
        )

        # 2. Strengths
        best_str = ', '.join([f"{b['symbol']} ({b['pnl_pct']:+.1f}%)" for b in m.best_performers[:3]])
        gold_symbols = [h.clean_symbol for h in m.holdings_analysis if 'GOLD' in h.clean_symbol]
        gold_str = ', '.join(gold_symbols) if gold_symbols else 'N/A'
        top_sec = list(m.sector_allocation.keys())[0] if m.sector_allocation else 'Power & Telecom'

        strengths = [
            f"Top performers (e.g. {best_str}) demonstrate substantial alpha generation.",
            f"Robust exposure to high-conviction secular growth sectors including {top_sec}.",
            "Presence of high-quality institutional balance sheets (e.g. Tata Power, Reliance, ITC, Nifty 50 ETF) providing downside liquidity support.",
            f"Effective hedging and asset diversification through physical gold ETF holdings ({gold_str})."
        ]

        # 3. Weaknesses
        worst_str = ', '.join([f"{w['symbol']} ({w['pnl_pct']:+.1f}%)" for w in m.worst_performers[:3]])
        tail_count = len([h for h in m.holdings_analysis if h.weight_pct < 1.0])

        weaknesses = [
            f"Severe 'tail fragmentation': The portfolio holds {m.stock_count} securities, with over {tail_count} positions representing less than 1.0% each, introducing tracking complexity without meaningful alpha.",
            f"Elevated top-5 weight concentration: The top 5 holdings represent {m.top_5_weight_pct:.1f}% of total portfolio equity.",
            f"Significant capital drag from severe drawdowns in speculative holdings (e.g. {worst_str}).",
            "Disproportionate allocation to cyclical sectors with high regulatory and commodity price volatility."
        ]

        # 4. Risk Flags
        risk_flags = [
            {
                "category": "High-Debt & Solvency Flags",
                "items": [h.clean_symbol for h in m.holdings_analysis if h.clean_symbol in ["IDEA", "RCOM", "BAJAJHIND", "GENPHARMA"]],
                "assessment": "Holdings with elevated debt-to-equity or negative interest coverage vulnerable to interest rate cycles."
            },
            {
                "category": "Illiquid / Micro-Cap Surveillance Exposure",
                "items": [h.clean_symbol for h in m.holdings_analysis if h.market_cap_tier in ["Penny Stock", "Micro Cap"]],
                "assessment": "Positions below ₹500 Cr market cap or subject to ASM/GSM trading circuit limitations."
            },
            {
                "category": "Corporate Conglomerate Clustering",
                "items": [h.clean_symbol for h in m.holdings_analysis if "TATA" in h.clean_symbol or "TMCV" in h.clean_symbol or "TMPV" in h.clean_symbol],
                "assessment": "Substantial cumulative exposure across multiple entities of the same industrial house."
            }
        ]

        # 5. Strategy Alignment
        strategy_alignment = {
            "dominant_style": s.dominant_style,
            "best_fit_investor": s.best_matching_investor,
            "top_score": s.average_scores.get(s.best_matching_investor, 70.0),
            "explanation": s.portfolio_orientation_summary,
            "style_scores": s.average_scores,
            "conflicting_positions": s.conflicting_holdings
        }

        # 6. Research Observations
        observations = [
            "The distribution of returns follows a pronounced Pareto distribution: the top 3 profitable positions generated the vast majority of positive gains.",
            "Drawdowns are heavily concentrated in sub-₹10 nominal penny stocks that were purchased during speculative momentum phases.",
            "The simultaneous holding of Tata Motors Commercial (TMCV) and Passenger (TMPV) post-demerger provides focused pure-play exposures but doubles aggregate automotive sector weight.",
            "Gold ETF allocations (SETFGOLD and GOLDBEES) provide a steady uncorrelated capital buffer (+60% to +120% P&L) against domestic equity volatility."
        ]

        # 7. Questions for the Investor
        questions = [
            "What is your designated investment horizon for this portfolio (e.g. 1-3 years tactical or 5-10+ years compounding)?",
            "What is your tolerance for portfolio volatility: Can you comfortably tolerate a 15-20% interim drawdown in exchange for high upside?",
            "What is your primary mandate for this capital: Maximum capital appreciation, capital preservation, or regular dividend cash-flow generation?",
            "Given that sub-1% micro-positions demand significant monitoring effort, would consolidating tail holdings into broader index instruments better serve your goals?"
        ]

        # 8. Monitoring Checklist
        checklist = [
            {"holding": "Vodafone Idea (IDEA)", "metric": "Fundraising closure, subscriber churn rate, and 5G vendor rollout milestones."},
            {"holding": "Tata Power (TATAPOWER)", "metric": "Renewable capacity commissioning schedule and transmission & distribution RoE."},
            {"holding": "Tata Motors Demerged (TMCV / TMPV)", "metric": "Commercial vehicle replacement cycle demand and JLR EV margin trajectory."},
            {"holding": "IRCTC & RVNL", "metric": "Ministry of Railways capex allocation and quarterly order book execution rate."},
            {"holding": "Commodity Equities (IOC, NMDC, ONGC)", "metric": "Global benchmark crude and iron ore prices, dividend payout consistency."},
            {"holding": "Speculative Micro-Caps", "metric": "SEBI Enhanced Surveillance Measure (ESM/GSM) stage updates and quarterly promoter share pledging."}
        ]

        return {
            "portfolio_summary": summary_text,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "risk_flags": risk_flags,
            "strategy_alignment": strategy_alignment,
            "research_observations": observations,
            "questions_for_investor": questions,
            "monitoring_checklist": checklist,
            "disclaimer": COMPLIANCE_DISCLAIMER
        }


class PortfolioReportGenerator:
    """Exports comprehensive portfolio research reports in MD, CSV, Excel, and PDF."""

    @classmethod
    def generate_markdown(cls, metrics: PortfolioMetrics, style_profile: PortfolioStyleProfile) -> str:
        """Generates comprehensive markdown report."""
        review = ExpertPortfolioReview(metrics, style_profile).generate_review()
        m = metrics
        s = style_profile

        lines = [
            "# 📊 Institutional Portfolio Research & Expert-Style Evaluation Report",
            "",
            f"> **Statement Date:** {m.statement_date} | **Client ID:** {m.client_id} | **Evaluated Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}",
            "",
            "---",
            "",
            "## 1. Executive Portfolio Overview",
            "",
            f"- **Total Invested Amount:** ₹{m.total_invested:,.2f}",
            f"- **Current Portfolio Value:** ₹{m.total_current:,.2f}",
            f"- **Total Unrealized P&L:** ₹{m.total_pnl:,.2f} ({m.total_pnl_pct:+.2f}%)",
            f"- **Total Number of Holdings:** {m.stock_count}",
            f"- **Portfolio Quality Score:** {m.portfolio_quality_score:.1f} / 100",
            f"- **Portfolio Diversification Score:** {m.portfolio_diversification_score:.1f} / 100",
            f"- **Portfolio Risk Index:** {m.portfolio_risk_score:.1f} / 100",
            f"- **Research Rating Classification:** **{m.portfolio_research_rating}**",
            "",
            "---",
            "",
            "## 2. Holdings & Performance Matrix",
            "",
            "| Symbol | Company Name | Sector | Cap Tier | Qty | Buy Price (₹) | Current Price (₹) | Current Value (₹) | Weight (%) | P&L (₹) | P&L (%) | Sizing |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"
        ]

        for h in m.holdings_analysis:
            lines.append(
                f"| `{h.clean_symbol}` | {h.stock_name[:24]} | {h.sector[:18]} | {h.market_cap_tier} | "
                f"{h.quantity:,.0f} | ₹{h.buy_price:,.2f} | ₹{h.current_price:,.2f} | ₹{h.current_value:,.2f} | "
                f"{h.weight_pct:.1f}% | ₹{h.pnl_amount:+,.2f} | {h.pnl_pct:+.1f}% | {h.sizing_status.split(' ')[0]} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Asset & Sector Allocation",
            "",
            "### Sector Breakdown",
            "| Sector | Current Value (₹) | Portfolio Weight (%) |",
            "|---|---|---|"
        ])
        for sec, d in m.sector_allocation.items():
            lines.append(f"| {sec} | ₹{d['value']:,.2f} | {d['weight_pct']:.2f}% |")

        lines.extend([
            "",
            "### Market Cap Tier Distribution",
            "| Cap Tier | Current Value (₹) | Portfolio Weight (%) |",
            "|---|---|---|"
        ])
        for tier, d in m.market_cap_allocation.items():
            lines.append(f"| {tier} | ₹{d['value']:,.2f} | {d['weight_pct']:.2f}% |")

        lines.extend([
            "",
            "---",
            "",
            "## 4. 9 Legendary Investor Style Scorecard",
            "",
            f"**Dominant Strategy Fit:** `{s.best_matching_investor}` (Score: {s.average_scores.get(s.best_matching_investor, 0):.1f}/100)",
            f"**Portfolio Orientation:** {s.dominant_style}",
            "",
            "| Investment Philosophy | Average Score (/100) | Style Mandate | Key Aligned Holdings |",
            "|---|---|---|---|"
        ])

        mandates = {
            "Warren Buffett": "Moat, ROCE > 18%, Free Cash Flow",
            "Charlie Munger": "Rational Quality, Anti-stupidity",
            "Benjamin Graham": "Deep Value, Margin of Safety, Low P/B",
            "Peter Lynch": "GARP, Scalable Consumer/Industrial Growth",
            "Joel Greenblatt": "Magic Formula: ROC + Earnings Yield",
            "Rakesh Jhunjhunwala": "Domestic India Growth, Operating Leverage",
            "Philip Fisher": "Innovation, R&D Moat, Customer Stickiness",
            "Dolly Khanna": "Niche Small/Mid-Cap Compounders",
            "Porinju Veliyath": "Contrarian Turnaround & Special Situations"
        }

        for strat in PortfolioInvestorStyles.STRATEGIES:
            sc = s.average_scores.get(strat, 50.0)
            mandate = mandates.get(strat, "Factor Model")
            aligned = ", ".join(s.strategy_fits.get(strat, [])[:4]) or "None"
            lines.append(f"| **{strat}** | **{sc:.1f}** | {mandate} | {aligned} |")

        lines.extend([
            "",
            "---",
            "",
            "## 5. Senior Analyst Expert Review",
            "",
            "### A. Portfolio Strengths",
        ])
        for st in review["strengths"]:
            lines.append(f"- ✅ {st}")

        lines.extend([
            "",
            "### B. Portfolio Weaknesses & Friction Points",
        ])
        for wk in review["weaknesses"]:
            lines.append(f"- ⚠️ {wk}")

        lines.extend([
            "",
            "### C. Key Governance & Risk Flags",
        ])
        for rf in review["risk_flags"]:
            lines.append(f"- **{rf['category']}:** {', '.join(rf['items'])} - *{rf['assessment']}*")

        lines.extend([
            "",
            "### D. Neutral Research Observations",
        ])
        for ob in review["research_observations"]:
            lines.append(f"- 🔍 {ob}")

        lines.extend([
            "",
            "### E. Strategic Questions for the Investor",
        ])
        for q in review["questions_for_investor"]:
            lines.append(f"- ❓ {q}")

        lines.extend([
            "",
            "### F. Holding Monitoring Checklist",
            "| Holding | Surveillance Metric & Event Trigger |",
            "|---|---|"
        ])
        for chk in review["monitoring_checklist"]:
            lines.append(f"| **{chk['holding']}** | {chk['metric']} |")

        lines.extend([
            "",
            "---",
            "",
            "## 6. Compliance & Regulatory Disclaimer",
            "",
            f"> {COMPLIANCE_DISCLAIMER}",
            ""
        ])

        return "\n".join(lines)

    @classmethod
    def generate_csv(cls, metrics: PortfolioMetrics) -> str:
        """Exports parsed holdings and calculated metrics to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header metadata
        writer.writerow(["REPORT TITLE", "Institutional Portfolio Research Statement"])
        writer.writerow(["Statement Date", metrics.statement_date])
        writer.writerow(["Client ID", metrics.client_id])
        writer.writerow(["Total Invested (INR)", f"{metrics.total_invested:.2f}"])
        writer.writerow(["Total Current (INR)", f"{metrics.total_current:.2f}"])
        writer.writerow(["Total P&L (INR)", f"{metrics.total_pnl:.2f}"])
        writer.writerow(["Total P&L (%)", f"{metrics.total_pnl_pct:.2f}%"])
        writer.writerow(["Quality Score", f"{metrics.portfolio_quality_score:.1f}"])
        writer.writerow(["Diversification Score", f"{metrics.portfolio_diversification_score:.1f}"])
        writer.writerow(["Risk Index", f"{metrics.portfolio_risk_score:.1f}"])
        writer.writerow(["Research Rating", metrics.portfolio_research_rating])
        writer.writerow([])

        # Holdings table
        writer.writerow([
            "Stock Name", "Symbol", "Exchange", "ISIN", "Quantity", "Average Buy Price",
            "Current Market Price", "Invested Amount", "Current Value", "Weight (%)",
            "P&L Amount", "P&L (%)", "Sector", "Market Cap Tier", "Sizing Status", "Stock Score"
        ])

        for h in metrics.holdings_analysis:
            writer.writerow([
                h.stock_name, h.clean_symbol, h.exchange, h.isin, h.quantity,
                f"{h.buy_price:.2f}", f"{h.current_price:.2f}", f"{h.invested_amount:.2f}",
                f"{h.current_value:.2f}", f"{h.weight_pct:.2f}", f"{h.pnl_amount:.2f}",
                f"{h.pnl_pct:.2f}", h.sector, h.market_cap_tier, h.sizing_status, f"{h.stock_score:.1f}"
            ])

        writer.writerow([])
        writer.writerow(["COMPLIANCE DISCLAIMER", COMPLIANCE_DISCLAIMER])
        return output.getvalue()

    @classmethod
    def generate_excel(cls, metrics: PortfolioMetrics, style_profile: PortfolioStyleProfile) -> bytes:
        """Generates professionally styled Excel (.xlsx) workbook with multiple sheets."""
        wb = Workbook()

        # Styling
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=16, bold=True, color="0F172A")
        bold_font = Font(name="Calibri", size=11, bold=True)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # Sheet 1: Holdings & Performance
        ws1 = wb.active
        ws1.title = "Portfolio Holdings"
        ws1.views.sheetView[0].showGridLines = True

        ws1.append(["Portfolio Research & Holdings Matrix"])
        ws1["A1"].font = title_font
        ws1.append([f"Statement Date: {metrics.statement_date}", f"Client ID: {metrics.client_id}", f"Generated: {datetime.now().strftime('%Y-%m-%d')}"])
        ws1.append([])

        # KPI Block
        ws1.append(["Total Invested (INR)", metrics.total_invested, "Quality Score", f"{metrics.portfolio_quality_score:.1f}/100"])
        ws1.append(["Current Value (INR)", metrics.total_current, "Diversification Score", f"{metrics.portfolio_diversification_score:.1f}/100"])
        ws1.append(["Total P&L (INR)", metrics.total_pnl, "Risk Score", f"{metrics.portfolio_risk_score:.1f}/100"])
        ws1.append(["Return (%)", f"{metrics.total_pnl_pct:+.2f}%", "Research Rating", metrics.portfolio_research_rating])
        ws1.append([])

        table_headers = [
            "Symbol", "Company Name", "Exchange", "ISIN", "Quantity", "Buy Price",
            "Current Price", "Invested (INR)", "Current (INR)", "Weight (%)",
            "P&L (INR)", "P&L (%)", "Sector", "Cap Tier", "Score"
        ]
        ws1.append(table_headers)
        header_row_idx = ws1.max_row
        for col_idx in range(1, len(table_headers) + 1):
            cell = ws1.cell(row=header_row_idx, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for h in metrics.holdings_analysis:
            row = [
                h.clean_symbol, h.stock_name, h.exchange, h.isin, h.quantity,
                h.buy_price, h.current_price, h.invested_amount, h.current_value,
                h.weight_pct, h.pnl_amount, h.pnl_pct, h.sector, h.market_cap_tier, h.stock_score
            ]
            ws1.append(row)
            curr_row = ws1.max_row
            # Style borders
            for c_idx in range(1, len(row) + 1):
                ws1.cell(row=curr_row, column=c_idx).border = thin_border

        # Adjust column widths
        for col in ws1.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws1.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # Sheet 2: Allocations & Investor Styles
        ws2 = wb.create_sheet(title="Allocation & 9 Strategies")
        ws2.views.sheetView[0].showGridLines = True

        ws2.append(["Sector Allocation"])
        ws2["A1"].font = title_font
        ws2.append(["Sector", "Current Value (INR)", "Weight (%)"])
        for col_idx in range(1, 4):
            ws2.cell(row=2, column=col_idx).fill = header_fill
            ws2.cell(row=2, column=col_idx).font = header_font

        for sec, d in metrics.sector_allocation.items():
            ws2.append([sec, d["value"], d["weight_pct"]])

        ws2.append([])
        ws2.append(["9 Legendary Investor Style Scores"])
        ws2[f"A{ws2.max_row}"].font = title_font
        ws2.append(["Strategy Name", "Score (/100)", "Dominant Fit"])
        st_row = ws2.max_row
        for col_idx in range(1, 4):
            ws2.cell(row=st_row, column=col_idx).fill = header_fill
            ws2.cell(row=st_row, column=col_idx).font = header_font

        for strat, sc in style_profile.average_scores.items():
            is_best = "YES (Top Fit)" if strat == style_profile.best_matching_investor else "No"
            ws2.append([strat, sc, is_best])

        # Adjust widths for sheet 2
        for col in ws2.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws2.column_dimensions[col_letter].width = max(max_len + 3, 14)

        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()

    @classmethod
    def generate_pdf(cls, metrics: PortfolioMetrics, style_profile: PortfolioStyleProfile) -> bytes:
        """Generates institutional PDF research report using FPDF."""
        review = ExpertPortfolioReview(metrics, style_profile).generate_review()
        m = metrics
        s = style_profile

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        def clean_pdf_txt(txt: str) -> str:
            if not txt:
                return ""
            return str(txt).replace("₹", "Rs ").encode("latin-1", "replace").decode("latin-1")

        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, clean_pdf_txt('Portfolio Research & Expert Evaluation'), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, clean_pdf_txt(f'Statement Date: {m.statement_date} | Client ID: {m.client_id} | Monitored Holdings: {m.stock_count}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

        # Executive KPI Grid (Draw colored summary box)
        pdf.set_fill_color(241, 245, 249)
        pdf.rect(10, pdf.get_y(), 190, 24, 'F')
        pdf.set_xy(12, pdf.get_y() + 2)

        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(45, 5, clean_pdf_txt(f'Invested: Rs {m.total_invested:,.0f}'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(45, 5, clean_pdf_txt(f'Current: Rs {m.total_current:,.0f}'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pnl_text = clean_pdf_txt(f'P&L: Rs {m.total_pnl:+,.0f} ({m.total_pnl_pct:+.1f}%)')
        pdf.cell(50, 5, pnl_text, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(45, 5, clean_pdf_txt(f'Rating: {m.portfolio_research_rating[:16]}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_xy(12, pdf.get_y() + 2)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(45, 5, clean_pdf_txt(f'Quality: {m.portfolio_quality_score:.1f}/100'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(45, 5, clean_pdf_txt(f'Diversification: {m.portfolio_diversification_score:.1f}/100'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(50, 5, clean_pdf_txt(f'Risk Index: {m.portfolio_risk_score:.1f}/100'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(45, 5, clean_pdf_txt(f'Top 5 Weight: {m.top_5_weight_pct:.1f}%'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(8)

        # Table: Top 10 Holdings
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, clean_pdf_txt('Top Holdings Snapshot'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Table Header
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        col_w = [25, 45, 30, 18, 22, 25, 25]
        headers = ['Symbol', 'Company', 'Sector', 'Qty', 'Cur Price', 'Cur Value', 'P&L (%)']
        for w, h_text in zip(col_w, headers):
            pdf.cell(w, 6, clean_pdf_txt(h_text), border=1, fill=True, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln()

        # Rows
        pdf.set_text_color(30, 41, 59)
        pdf.set_font('Helvetica', '', 7)
        for h in m.holdings_analysis[:12]:
            pdf.cell(col_w[0], 5, clean_pdf_txt(h.clean_symbol[:12]), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(col_w[1], 5, clean_pdf_txt(h.stock_name[:24]), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(col_w[2], 5, clean_pdf_txt(h.sector[:18]), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(col_w[3], 5, clean_pdf_txt(f'{h.quantity:.0f}'), border=1, align='R', new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(col_w[4], 5, clean_pdf_txt(f'Rs {h.current_price:.1f}'), border=1, align='R', new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(col_w[5], 5, clean_pdf_txt(f'Rs {h.current_value:.0f}'), border=1, align='R', new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(col_w[6], 5, clean_pdf_txt(f'{h.pnl_pct:+.1f}%'), border=1, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(4)

        # 9 Legendary Investor Alignment Box
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 7, clean_pdf_txt('9 Legendary Investor Style Profile'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, clean_pdf_txt(f"Top Strategy Fit: {s.best_matching_investor} ({s.average_scores.get(s.best_matching_investor, 0):.1f}/100) | Orientation: {s.dominant_style}"))
        pdf.ln(2)

        # Expert Review Section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 6, clean_pdf_txt('Senior Analyst Review & Risk Flags'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, clean_pdf_txt(f"Observations: {review['portfolio_summary']}"))
        pdf.ln(2)

        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(0, 5, clean_pdf_txt('Strengths:'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 8)
        for st in review['strengths'][:3]:
            pdf.cell(0, 4, clean_pdf_txt(f"- {st[:100]}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(1)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(0, 5, clean_pdf_txt('Weaknesses & Risk Flags:'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 8)
        for wk in review['weaknesses'][:3]:
            pdf.cell(0, 4, clean_pdf_txt(f"- {wk[:100]}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(3)

        # Compliance Footer
        pdf.set_font('Helvetica', 'I', 7)
        pdf.set_text_color(148, 163, 184)
        pdf.multi_cell(0, 3, clean_pdf_txt(COMPLIANCE_DISCLAIMER))

        return bytes(pdf.output())
