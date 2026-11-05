"""Report generation utilities: Markdown, CSV, and PDF export."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fpdf import FPDF

from src.utils.helpers import format_inr, format_percentage


class MarkdownReportGenerator:
    """Generates detailed Markdown research reports."""

    @staticmethod
    def generate_header(title: str, disclaimer: str) -> str:
        return f"# {title}\n\n{disclaimer}\n\n---\n\n"

    @staticmethod
    def generate_executive_summary(total_stocks: int, date_str: str, market_overview: str) -> str:
        return (
            f"## Executive Summary\n\n"
            f"**Report Date:** {date_str}\n"
            f"**Stocks Analyzed:** {total_stocks}\n\n"
            f"{market_overview}\n\n"
        )

    @staticmethod
    def generate_ranked_table(stocks: List[Dict[str, Any]]) -> str:
        """Creates a markdown table of ranked stocks."""
        header = "| Rank | Symbol | Name | Sector | Market Cap | Score | Quality | Growth | Valuation | Momentum | Catalyst | Risk |\n"
        header += "|------|--------|------|--------|------------|-------|---------|--------|-----------|----------|----------|------|\n"
        rows = []
        for s in stocks:
            rows.append(
                f"| {s.get('rank', 'N/A')} | {s.get('symbol', 'N/A')} | {s.get('name', 'N/A')[:20]} | "
                f"{s.get('sector', 'N/A')[:15]} | {s.get('market_cap_str', 'N/A')} | "
                f"{s.get('composite_score', 0):.1f} | {s.get('quality_score', 0):.1f} | "
                f"{s.get('growth_score', 0):.1f} | {s.get('valuation_score', 0):.1f} | "
                f"{s.get('momentum_score', 0):.1f} | {s.get('catalyst_score', 0):.1f} | "
                f"{s.get('risk_score', 0):.1f} |"
            )
        return header + "\n".join(rows) + "\n\n"

    @staticmethod
    def generate_detailed_stock_report(stock: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generates the full detailed report for a single stock."""
        lines = []
        symbol = stock.get('symbol', 'UNKNOWN')
        name = stock.get('name', 'Unknown Company')
        sector = stock.get('sector', 'N/A')
        market_cap_str = stock.get('market_cap_str', 'N/A')
        rank = stock.get('rank', 'N/A')
        score = stock.get('composite_score', 0)

        lines.append(f"## {rank}. {name} — NSE: {symbol.replace('.NS','')} / BSE: {symbol.replace('.BO','')}\n")
        lines.append(f"**Rank:** {rank}  \n")
        lines.append(f"**Composite Score:** {score:.1f}/100  \n")
        lines.append(f"**Sector:** {sector}  \n")
        lines.append(f"**Market Cap:** {market_cap_str}  \n")
        lines.append(f"**Liquidity:** {stock.get('liquidity', 'N/A')}  \n\n")

        # Investment Thesis
        lines.append("### Investment Thesis\n")
        lines.append(f"{stock.get('thesis', 'No thesis available.')}\n\n")

        # Score Breakdown
        lines.append("### Score Breakdown\n\n")
        lines.append("| Component | Score | Weight | Contribution |\n")
        lines.append("|---|---:|---:|---:|\n")
        weights = config.get('scoring_weights', {})
        components = [
            ("Quality", stock.get('quality_score', 0), weights.get('quality', 0.30)),
            ("Growth", stock.get('growth_score', 0), weights.get('growth', 0.20)),
            ("Valuation", stock.get('valuation_score', 0), weights.get('valuation', 0.15)),
            ("Momentum", stock.get('momentum_score', 0), weights.get('momentum', 0.15)),
            ("Catalysts", stock.get('catalyst_score', 0), weights.get('catalyst', 0.10)),
            ("Risk Penalty", stock.get('risk_score', 0), weights.get('risk_penalty', 0.10)),
        ]
        total_contrib = 0
        for name_c, score_c, weight_c in components:
            if name_c == "Risk Penalty":
                contrib = -score_c * weight_c
            else:
                contrib = score_c * weight_c
            total_contrib += contrib
            lines.append(f"| {name_c} | {score_c:.1f} | {weight_c*100:.0f}% | {contrib:+.2f} |\n")
        
        lines.append(f"| **Total** | | | **{total_contrib:.2f}** |\n\n")

        # Bull Case
        bull_points = stock.get('bull_case', [])
        if bull_points:
            lines.append("### Bull Case\n")
            for p in bull_points:
                lines.append(f"- {p}\n")
            lines.append("\n")

        # Bear Case
        bear_points = stock.get('bear_case', [])
        if bear_points:
            lines.append("### Bear Case\n")
            for p in bear_points:
                lines.append(f"- {p}\n")
            lines.append("\n")

        # Key Risks
        risks = stock.get('risks', [])
        if risks:
            lines.append("### Key Risks\n")
            for r in risks:
                lines.append(f"- {r}\n")
            lines.append("\n")

        # Thesis Invalidation Conditions
        invalidation = stock.get('invalidation_conditions', [])
        if invalidation:
            lines.append("### Thesis Invalidation Conditions\n")
            for c in invalidation:
                lines.append(f"- {c}\n")
            lines.append("\n")

        # Evidence Citations
        citations = stock.get('citations', [])
        if citations:
            lines.append("### Evidence & Citations\n")
            for c in citations:
                lines.append(f"- [{c.get('title', 'Source')}]({c.get('url', '#')}) — {c.get('date', 'N/A')}  \n")
            lines.append("\n")

        return "".join(lines)

    @staticmethod
    def save_report(content: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


class CSVExporter:
    """Exports ranked watchlist to CSV."""

    @staticmethod
    def export(stocks: List[Dict[str, Any]], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not stocks:
            return
        fieldnames = list(stocks[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stocks)


class PDFReportGenerator(FPDF):
    """Simple PDF Report Generator using fpdf2."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, "AI Stock Research Report - Confidential", align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title_page(self, title: str, date_str: str, disclaimer: str):
        self.add_page()
        self.set_font("Helvetica", "B", 24)
        self.ln(40)
        self.cell(0, 15, title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 12)
        self.cell(0, 10, f"Report Date: {date_str}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(20)
        self.set_font("Helvetica", "B", 10)
        self.multi_cell(0, 6, disclaimer, align="C")

    def _sanitize_text(self, text: str) -> str:
        """Replace Unicode characters that can't be encoded in latin-1."""
        return text.replace('\u20b9', 'Rs.').replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    
    def add_table(self, headers: List[str], data: List[List[str]], col_widths: List[float]):
        self.set_font("Helvetica", "B", 7)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, self._sanitize_text(h), border=1, align="C")
        self.ln()
        self.set_font("Helvetica", "", 7)
        for row in data:
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 5, self._sanitize_text(str(cell)[:30]), border=1)
            self.ln()

    def add_section(self, title: str, body: str):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, body)
        self.ln(4)

    def save(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output(str(output_path))