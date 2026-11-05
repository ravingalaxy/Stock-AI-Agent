"""
Unit and Integration Tests for IPO Analysis Module & 9 Legendary Strategies.
"""

from datetime import date
from django.test import TestCase, Client
from django.urls import reverse

from src.analysis.ipo_analyzer import IPOStrategyEvaluator, IPOData
from apps.ipo.models import IPOListing
from apps.ipo.services import seed_ipo_universe_if_empty


class TestIPOStrategyEvaluator(TestCase):
    """Test suite for the 30+ year institutional IPO evaluation engine."""

    def setUp(self):
        self.evaluator = IPOStrategyEvaluator()
        self.sample_ipo = IPOData(
            company_name="Premier CleanTech Limited",
            symbol="CLEANTECH",
            sector="Renewable Energy",
            price_band_low=500.0,
            price_band_high=540.0,
            lot_size=25,
            issue_size_cr=1200.0,
            fresh_issue_cr=900.0,   # 75% Fresh Issue
            ofs_cr=300.0,           # 25% OFS
            revenue_3y_cagr=0.32,
            pat_3y_cagr=0.45,
            operating_margin=21.0,
            net_margin=14.5,
            pre_roe=24.0,
            pre_roce=26.5,
            debt_to_equity=0.25,
            interest_coverage=14.0,
            fcf_positive=True,
            post_pe=22.0,
            post_pb=3.1,
            industry_pe=32.0,       # Trading at discount to peers
            gmp=180.0,
            gmp_percent=33.3,
            qib_subscription=45.0,
            nii_subscription=28.0,
            retail_subscription=12.0,
            anchor_quality="High",
            promoter_holding_pre=82.0,
            promoter_holding_post=68.0,
            litigation_flag=False,
            auditor_qualification=False,
            objects_of_issue="Capex for high-efficiency solar cell manufacturing facility"
        )

    def test_evaluate_all_nine_strategies(self):
        """Verify that all 9 legendary investor philosophies return complete evaluations."""
        result = self.evaluator.evaluate_all(self.sample_ipo)
        strategies = result["strategies"]

        expected_philosophies = [
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

        self.assertEqual(len(strategies), 9)
        for name in expected_philosophies:
            slug = name.lower().replace(" ", "_")
            self.assertIn(slug, strategies, f"Missing strategy {name}")
            strat = strategies[slug]
            self.assertEqual(strat["philosophy"], name)
            self.assertIn(strat["label"], ["Apply / Buy", "Hold / Neutral", "Avoid"])
            self.assertGreaterEqual(strat["score"], 0.0)
            self.assertLessEqual(strat["score"], 100.0)
            self.assertTrue(len(strat["reason"]) > 5)
            self.assertTrue(len(strat["key_risks"]) >= 1)

    def test_composite_scoring_and_recommendation(self):
        """Verify composite score weighting and institutional recommendation."""
        result = self.evaluator.evaluate_all(self.sample_ipo)
        self.assertGreaterEqual(result["composite_score"], 70.0)
        self.assertIn("Apply", result["recommendation"])
        self.assertIn("valuation", result["subscores"])
        self.assertIn("structure", result["subscores"])

    def test_three_thesis_invalidations_enforced(self):
        """Verify that at least 3 explicit thesis failure conditions are generated."""
        result = self.evaluator.evaluate_all(self.sample_ipo)
        invalidations = result["thesis_invalidations"]
        self.assertGreaterEqual(len(invalidations), 3)
        for inv in invalidations:
            self.assertTrue(isinstance(inv, str) and len(inv) > 15)

    def test_heavy_ofs_and_poor_governance_penalty(self):
        """Ensure heavy OFS and litigation trigger immediate penalty."""
        bad_ipo = IPOData(
            company_name="Dumping Promoters Ltd",
            symbol="DUMP",
            sector="General Services",
            price_band_low=100.0,
            price_band_high=100.0,
            lot_size=100,
            issue_size_cr=1000.0,
            fresh_issue_cr=100.0,   # 10% Fresh
            ofs_cr=900.0,           # 90% OFS exit
            revenue_3y_cagr=0.05,
            pat_3y_cagr=-0.02,
            operating_margin=4.0,
            net_margin=1.5,
            pre_roe=5.0,
            pre_roce=6.0,
            debt_to_equity=1.8,
            interest_coverage=1.5,
            fcf_positive=False,
            post_pe=60.0,
            post_pb=7.5,
            industry_pe=20.0,       # 3x more expensive than peers
            gmp=-10.0,
            gmp_percent=-10.0,
            litigation_flag=True,
            auditor_qualification=True,
            promoter_holding_post=35.0
        )
        res = self.evaluator.evaluate_all(bad_ipo)
        self.assertLess(res["composite_score"], 45.0)
        self.assertEqual(res["recommendation"], "Avoid")
        self.assertEqual(res["strategies"]["warren_buffett"]["label"], "Avoid")
        self.assertEqual(res["strategies"]["charlie_munger"]["label"], "Avoid")


class TestIPODjangoModelsAndViews(TestCase):
    """Test suite for IPO Django database models, views, and REST APIs."""

    def setUp(self):
        self.client = Client()
        seed_ipo_universe_if_empty()

    def test_ipo_seeding_and_model_properties(self):
        """Test that seed_ipo_universe_if_empty populates listings and calculated properties."""
        count = IPOListing.objects.count()
        self.assertGreaterEqual(count, 5)

        waaree = IPOListing.objects.filter(symbol="WAAREE").first()
        self.assertIsNotNone(waaree)
        self.assertGreater(waaree.fresh_ratio_pct, 70.0)
        self.assertGreater(waaree.estimated_listing_price, waaree.price_band_high)
        self.assertGreater(waaree.minimum_investment, 10000.0)
        self.assertEqual(len(waaree.strategies), 9)
        self.assertGreaterEqual(len(waaree.thesis_invalidations), 3)

    def test_ipo_dashboard_view(self):
        """Test IPO Dashboard rendering and status filtering."""
        response = self.client.get(reverse('ipo:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Institutional IPO Analysis")
        self.assertContains(response, "Bombay Coated")

        # Listed view contains recently listed entities
        res_listed = self.client.get(reverse('ipo:dashboard') + '?view=listed')
        self.assertEqual(res_listed.status_code, 200)
        self.assertContains(res_listed, "Jio Platforms")

        # Test filter by status=Open
        res_open = self.client.get(reverse('ipo:dashboard') + '?status=open')
        self.assertEqual(res_open.status_code, 200)

    def test_ipo_detail_view(self):
        """Test individual IPO deep dive research page."""
        response = self.client.get(reverse('ipo:detail', kwargs={'symbol': 'WAAREE'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Waaree Energies Limited")
        self.assertContains(response, "Warren Buffett")
        self.assertContains(response, "Charlie Munger")
        self.assertContains(response, "Peter Lynch")
        self.assertContains(response, "At Least 3 Thesis Invalidation Conditions")

    def test_api_ipo_endpoints(self):
        """Test JSON REST endpoints for IPO list and detail."""
        res_list = self.client.get(reverse('ipo:api_list'))
        self.assertEqual(res_list.status_code, 200)
        json_data = res_list.json()
        self.assertEqual(json_data["status"], "success")
        self.assertGreater(json_data["count"], 0)

        res_drf = self.client.get('/api/v1/ipos/')
        self.assertEqual(res_drf.status_code, 200)
        self.assertGreater(res_drf.json()["count"], 0)

    def test_jio_and_ongoing_ipos_available(self):
        """Verify that Reliance Jio and ongoing IPOs are seeded and discoverable."""
        jio = IPOListing.objects.filter(symbol="JIO").first()
        self.assertIsNotNone(jio, "Reliance Jio (JIO) must be present in the IPO universe")
        self.assertIn("Reliance Jio", jio.company_name)
        self.assertEqual(len(jio.strategies), 9)
        self.assertGreaterEqual(len(jio.thesis_invalidations), 3)

        # Test Listed View contains Jio Platforms
        res_listed_view = self.client.get(reverse('ipo:dashboard') + '?view=listed')
        self.assertEqual(res_listed_view.status_code, 200)
        self.assertContains(res_listed_view, "Jio Platforms")

        # Test Active Dashboard contains ongoing issues
        res_active = self.client.get(reverse('ipo:dashboard'))
        self.assertEqual(res_active.status_code, 200)
        self.assertContains(res_active, "Bombay Coated")

        # Test Upcoming filtering (Genuine pipeline like Imagine Marketing / boAt and Zepto)
        res_upcoming = self.client.get(reverse('ipo:dashboard') + '?status=upcoming')
        self.assertEqual(res_upcoming.status_code, 200)
        self.assertContains(res_upcoming, "Imagine Marketing")
        self.assertContains(res_upcoming, "Zepto")

        # Listed IPOs are now excluded from the dashboard (only Upcoming/Open/Ongoing shown)
        res_listed = self.client.get(reverse('ipo:dashboard') + '?status=listed')
        self.assertEqual(res_listed.status_code, 200)
        self.assertNotContains(res_listed, "HDB Financial Services")
        self.assertNotContains(res_listed, "Swiggy Limited")
        self.assertNotContains(res_listed, "Afcons Infrastructure")

        # Test JIO Detail View
        res_jio_detail = self.client.get(reverse('ipo:detail', kwargs={'symbol': 'JIO'}))
        self.assertEqual(res_jio_detail.status_code, 200)
        self.assertContains(res_jio_detail, "Jio Platforms")

        # Test Global Search Autocomplete for 'jio'
        res_search = self.client.get(reverse('market:search_stocks') + '?q=jio')
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertTrue(any("JIO" in item["clean_symbol"] for item in search_data["results"]))
