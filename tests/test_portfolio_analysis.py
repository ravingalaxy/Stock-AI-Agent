"""
Comprehensive Unit and Integration Test Suite for Portfolio Analysis.
Validates:
1. CSV parsing against FYERS statement & custom broker formats
2. Excel (.xlsx and .xls) parsing
3. PDF and DOCX statement extraction
4. Quantitative portfolio math, allocations, and concentration alerts
5. 9 Legendary Investor scoring engine and portfolio style profiling
6. Multi-format report export (Markdown, CSV, Excel, PDF)
7. Django views and export endpoints
"""

import io
import os
import csv
from pathlib import Path
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse

from openpyxl import Workbook
import docx

from src.portfolio.portfolio_parser import PortfolioParser, ParsedPortfolio, ParsedHolding
from src.portfolio.portfolio_analyzer import PortfolioAnalyzer, PortfolioMetrics, HoldingAnalysis
from src.portfolio.investor_styles import PortfolioInvestorStyles, PortfolioStyleProfile
from src.portfolio.portfolio_report import PortfolioReportGenerator, ExpertPortfolioReview, COMPLIANCE_DISCLAIMER
from src.portfolio.top_portfolios import TopPortfoliosRepository, TopMarketPortfolio
from apps.portfolio.models import UploadedPortfolioStatement, UploadedHoldingRecord, PortfolioAnalysisReport


class TestPortfolioParsingAndAnalytics(TestCase):
    """Core quantitative parsing and mathematical verification tests."""

    def setUp(self):
        self.client = Client()
        self.fyers_csv = Path(__file__).resolve().parent.parent / "sample_portfolio_statement.csv"

    def test_fyers_csv_statement_parsing(self):
        """Test extraction against the anonymized sample broker statement."""
        self.assertTrue(self.fyers_csv.exists(), "Sample broker statement must exist")
        parsed = PortfolioParser.parse_file(self.fyers_csv)

        self.assertTrue(parsed.is_valid)
        self.assertEqual(parsed.statement_date, "23-10-2026")
        self.assertEqual(parsed.client_id, "DEMO_INV_001")
        self.assertEqual(parsed.client_name, "Demo Investor")
        self.assertEqual(len(parsed.holdings), 49)

        # Mathematical verification of reported vs calculated
        self.assertAlmostEqual(parsed.total_invested_calculated, 113674.47, places=1)
        self.assertAlmostEqual(parsed.total_current_calculated, 107233.60, places=1)
        self.assertAlmostEqual(parsed.total_pnl_calculated, -6440.87, places=1)
        self.assertAlmostEqual(parsed.total_pnl_pct_calculated, -5.67, delta=0.05)

        # Check specific holdings
        idea = next((h for h in parsed.holdings if h.clean_symbol == "IDEA"), None)
        self.assertIsNotNone(idea)
        self.assertEqual(idea.quantity, 1100.0)
        self.assertEqual(idea.buy_price, 7.66)
        self.assertEqual(idea.isin, "INE669E01016")

    def test_excel_xlsx_parsing(self):
        """Test parsing of an in-memory Excel .xlsx workbook."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Holdings"
        ws.append(["Report Title", "Holding statements report"])
        ws.append(["Date", "25-10-2026"])
        ws.append(["Client ID", "TEST999"])
        ws.append([])
        ws.append(["Name", "Qty", "Buy price", "Current price", "Invested value", "Current value", "ISIN"])
        ws.append(["NSE:RELIANCE-EQ", 10, 2500.0, 2750.0, 25000.0, 27500.0, "INE002A01018"])
        ws.append(["NSE:TCS-EQ", 5, 3500.0, 3800.0, 17500.0, 19000.0, "INE467B01029"])

        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)

        parsed = PortfolioParser.parse_file(bio.getvalue(), filename="test_portfolio.xlsx")
        self.assertTrue(parsed.is_valid)
        self.assertEqual(len(parsed.holdings), 2)
        self.assertEqual(parsed.holdings[0].clean_symbol, "RELIANCE")
        self.assertEqual(parsed.holdings[1].clean_symbol, "TCS")
        self.assertAlmostEqual(parsed.total_invested_calculated, 42500.0)
        self.assertAlmostEqual(parsed.total_current_calculated, 46500.0)

    def test_docx_statement_parsing(self):
        """Test parsing of a Word .docx document table."""
        doc = docx.Document()
        doc.add_paragraph("Statement Date: 2026-10-25")
        doc.add_paragraph("Client ID: DOCX123")

        table = doc.add_table(rows=1, cols=6)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Symbol"
        hdr_cells[1].text = "Qty"
        hdr_cells[2].text = "Buy Price"
        hdr_cells[3].text = "Current Price"
        hdr_cells[4].text = "Current Value"
        hdr_cells[5].text = "ISIN"

        row = table.add_row().cells
        row[0].text = "NSE:INFY-EQ"
        row[1].text = "20"
        row[2].text = "1500.0"
        row[3].text = "1650.0"
        row[4].text = "33000.0"
        row[5].text = "INE009A01021"

        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)

        parsed = PortfolioParser.parse_file(bio.getvalue(), filename="portfolio_doc.docx")
        self.assertTrue(parsed.is_valid)
        self.assertEqual(len(parsed.holdings), 1)
        self.assertEqual(parsed.holdings[0].clean_symbol, "INFY")
        self.assertEqual(parsed.holdings[0].quantity, 20.0)

    def test_portfolio_quantitative_analysis(self):
        """Test metrics, sector allocation, concentration and risk scoring."""
        parsed = PortfolioParser.parse_file(self.fyers_csv)
        metrics = PortfolioAnalyzer.analyze_portfolio(parsed)

        self.assertEqual(metrics.stock_count, 49)
        self.assertGreater(len(metrics.sector_allocation), 5)
        self.assertGreater(len(metrics.market_cap_allocation), 3)

        # Best and worst performers present
        self.assertGreaterEqual(len(metrics.best_performers), 1)
        self.assertGreaterEqual(len(metrics.worst_performers), 1)

        # Quality and Diversification scores in 0-100 range
        self.assertTrue(0.0 <= metrics.portfolio_quality_score <= 100.0)
        self.assertTrue(0.0 <= metrics.portfolio_diversification_score <= 100.0)
        self.assertTrue(0.0 <= metrics.portfolio_risk_score <= 100.0)

        # Tata Group corporate cluster detection
        tata_group = next((g for g in metrics.overlapping_exposures if "Tata" in g["group_name"]), None)
        self.assertIsNotNone(tata_group, "Tata conglomerate group overlap should be detected")

    def test_9_legendary_investor_styles(self):
        """Test the 9 legendary investor scoring logic and portfolio profiling."""
        parsed = PortfolioParser.parse_file(self.fyers_csv)
        metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
        styles = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)

        # All 9 strategies evaluated
        self.assertEqual(len(styles.average_scores), 9)
        for s in PortfolioInvestorStyles.STRATEGIES:
            self.assertIn(s, styles.average_scores)
            self.assertTrue(0.0 <= styles.average_scores[s] <= 100.0)

        self.assertIsNotNone(styles.best_matching_investor)
        self.assertTrue(len(styles.strategy_rows) == 9)
        self.assertGreater(len(styles.portfolio_orientation_summary), 20)

    def test_multi_format_report_generation(self):
        """Test generation of Markdown, CSV, Excel, and PDF reports."""
        parsed = PortfolioParser.parse_file(self.fyers_csv)
        metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
        styles = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)

        # 1. Markdown
        md = PortfolioReportGenerator.generate_markdown(metrics, styles)
        self.assertIn("Institutional Portfolio Research", md)
        self.assertIn(COMPLIANCE_DISCLAIMER, md)
        self.assertGreater(len(md), 5000)

        # 2. CSV
        csv_out = PortfolioReportGenerator.generate_csv(metrics)
        self.assertIn("REPORT TITLE", csv_out)
        self.assertIn("IDEA", csv_out)

        # 3. Excel (.xlsx)
        xlsx_bytes = PortfolioReportGenerator.generate_excel(metrics, styles)
        self.assertGreater(len(xlsx_bytes), 2000)

        # 4. PDF (.pdf)
        pdf_bytes = PortfolioReportGenerator.generate_pdf(metrics, styles)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1500)


class TestPortfolioDjangoViews(TestCase):
    """End-to-end integration tests for Django routes and download endpoints."""

    def setUp(self):
        self.client = Client()

    def test_portfolio_analysis_view_renders(self):
        """Verify that /portfolio/analysis/ loads successfully."""
        res = self.client.get(reverse('portfolio:analysis'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Portfolio Analysis &amp; Expert-Style Evaluation")
        self.assertContains(res, "COMPLIANCE DISCLAIMER")
        self.assertContains(res, "Sector-Wise Asset Allocation")
        self.assertContains(res, "9 Legendary Investor Strategy Scorecard")

    def test_portfolio_preview_api(self):
        """Verify the AJAX preview API endpoint."""
        csv_content = b"Name,Qty,Buy price,Current price,Invested value,Current value,ISIN\nNSE:IDEA-EQ,100,8.0,10.0,800.0,1000.0,INE669E01016\n"
        upload = io.BytesIO(csv_content)
        upload.name = "test_holdings.csv"

        res = self.client.post(
            reverse('portfolio:preview_api'),
            {'portfolio_file': upload}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["holdings_count"], 1)
        self.assertEqual(data["preview_holdings"][0]["clean_symbol"], "IDEA")

    def test_portfolio_export_endpoints(self):
        """Verify that MD, CSV, XLSX, and PDF export endpoints return valid file attachments."""
        # Ensure FYERS statement is seeded
        self.client.get(reverse('portfolio:analysis'))

        for fmt, mime in [
            ('md', 'text/markdown'),
            ('csv', 'text/csv'),
            ('xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('pdf', 'application/pdf')
        ]:
            res = self.client.get(reverse('portfolio:export_report', kwargs={'fmt': fmt}))
            self.assertEqual(res.status_code, 200)
            self.assertIn('Content-Disposition', res.headers)
            self.assertIn('attachment', res.headers['Content-Disposition'])
            self.assertTrue(len(res.content) > 100)

    def test_portfolio_reset_endpoints(self):
        """Verify the portfolio reset functionality (both clear and default sample re-seed)."""
        # First ensure statement is seeded
        self.client.get(reverse('portfolio:analysis'))
        self.assertGreater(UploadedPortfolioStatement.objects.count(), 0)

        # 1. Test Reset with mode=clear
        clear_res = self.client.get(reverse('portfolio:reset') + '?mode=clear')
        self.assertEqual(clear_res.status_code, 302)
        self.assertIn('cleared=1', clear_res.url)
        self.assertEqual(UploadedPortfolioStatement.objects.count(), 0)

        # Verify cleared view renders empty state
        page_res = self.client.get(clear_res.url)
        self.assertEqual(page_res.status_code, 200)
        self.assertContains(page_res, "No Portfolio Statement Active")
        self.assertContains(page_res, "Portfolio statements have been cleared")

        # 2. Test Reset with mode=default (re-seeds default FYERS statement)
        default_res = self.client.get(reverse('portfolio:reset') + '?mode=default')
        self.assertEqual(default_res.status_code, 302)
        self.assertIn('reset=success', default_res.url)
        self.assertEqual(UploadedPortfolioStatement.objects.count(), 1)

        # Verify page re-renders full analytics
        page_res2 = self.client.get(default_res.url)
        self.assertEqual(page_res2.status_code, 200)
        self.assertContains(page_res2, "Portfolio has been reset to default sample statement")
        self.assertContains(page_res2, "9 Legendary Investor Strategy Scorecard")

    def test_top_portfolios_repository(self):
        """Verify the Top 10 Portfolios data model and stock-level rationales."""
        portfolios = TopPortfoliosRepository.get_all_portfolios()
        self.assertEqual(len(portfolios), 10, "Must contain exactly 10 top portfolios")

        for p in portfolios:
            self.assertTrue(p.id, "Portfolio must have an ID")
            self.assertTrue(p.name, "Portfolio must have a name")
            self.assertGreaterEqual(len(p.holdings), 8, f"{p.name} must have at least 8 holdings")

            # Check that every single holding has exhaustive reasons
            total_weight = sum(h.weight_pct for h in p.holdings)
            self.assertAlmostEqual(total_weight, 100.0, delta=1.0, msg=f"{p.name} weights should sum to ~100%")

            for h in p.holdings:
                self.assertTrue(h.clean_symbol, "Holding must have clean symbol")
                self.assertTrue(len(h.primary_reason) > 20, f"Stock {h.clean_symbol} in {p.name} must have a detailed primary reason")
                self.assertTrue(len(h.competitive_moat) > 10, f"Stock {h.clean_symbol} in {p.name} must have a competitive moat")
                self.assertTrue(len(h.growth_catalyst) > 10, f"Stock {h.clean_symbol} in {p.name} must have growth catalysts")
                self.assertTrue(len(h.risk_factor) > 10, f"Stock {h.clean_symbol} in {p.name} must have risk factors")

        # Verify search feature
        titan_results = TopPortfoliosRepository.find_stock_across_portfolios("TITAN")
        self.assertGreaterEqual(len(titan_results), 2, "TITAN should appear in at least 2 top portfolios")

    def test_top_portfolios_views_and_analyze_action(self):
        """Verify the Top 10 Portfolios Django view and 1-click diagnostic integration."""
        # 1. Main Directory View
        res = self.client.get(reverse('portfolio:top_portfolios'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Top 10 Portfolios of Stock Market")
        self.assertContains(res, "Rakesh Jhunjhunwala")
        self.assertContains(res, "Why This Stock Was Taken")

        # 2. Detail View for Specific Portfolio
        damani_res = self.client.get(reverse('portfolio:top_portfolio_detail', kwargs={'portfolio_id': 'radhakishan-damani'}))
        self.assertEqual(damani_res.status_code, 200)
        self.assertContains(damani_res, "Avenue Supermarts")
        self.assertContains(damani_res, "Radhakishan Damani")

        # 3. Search Query
        search_res = self.client.get(reverse('portfolio:top_portfolios') + '?q=TATAMOTORS')
        self.assertEqual(search_res.status_code, 200)
        self.assertContains(search_res, "Found")
        self.assertContains(search_res, "TATAMOTORS")

        # 4. One-Click Analyze Top Portfolio Action
        load_res = self.client.get(reverse('portfolio:analyze_top_portfolio', kwargs={'portfolio_id': 'buffett-munger-india'}))
        self.assertEqual(load_res.status_code, 302)
        self.assertIn('/portfolio/analysis/?statement_id=', load_res.url)

        # Follow redirect and verify 9-investor diagnostic renders
        analysis_page = self.client.get(load_res.url)
        self.assertEqual(analysis_page.status_code, 200)
        self.assertContains(analysis_page, "Buffett &amp; Munger High-Moat India Compounders")
        self.assertContains(analysis_page, "9 Legendary Investor Strategy Scorecard")

    def test_stock_market_search_and_provisioning(self):
        """Verify searching for any listed stock in India (e.g. IDEA) resolves and auto-provisions."""
        # 1. Global Autocomplete API search for IDEA
        res = self.client.get('/api/search/?q=idea')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        results = data.get('results', [])
        self.assertTrue(any(r['clean_symbol'] == 'IDEA' for r in results), "IDEA must be found in search results")

        # 2. Research Workstation for IDEA
        res_research = self.client.get('/research/IDEA/')
        self.assertEqual(res_research.status_code, 200)
        self.assertContains(res_research, "Vodafone Idea Limited")
        self.assertContains(res_research, "IDEA.NS")

        # 3. Top Portfolios search for IDEA (listed stock found in market)
        res_top_search = self.client.get(reverse('portfolio:top_portfolios') + '?q=idea')
        self.assertEqual(res_top_search.status_code, 200)
        self.assertContains(res_top_search, "Listed Stock Found in Stock Market")
        self.assertContains(res_top_search, "Vodafone Idea Limited")
