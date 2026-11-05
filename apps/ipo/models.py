"""
Django Models for Initial Public Offerings (IPO) Surveillance and Evaluation.
"""

import json
from django.db import models


class IPOListing(models.Model):
    """Institutional entity representing an NSE or BSE Initial Public Offering."""

    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Open', 'Currently Open / Subscribed'),
        ('Closed', 'Issue Closed (Allotment Pending)'),
        ('Listed', 'Recently Listed'),
    ]

    CATEGORY_CHOICES = [
        ('Mainboard', 'Mainboard IPO'),
        ('SME', 'SME Exchange IPO'),
    ]

    company_name = models.CharField(max_length=255, db_index=True)
    symbol = models.CharField(max_length=50, unique=True, db_index=True)
    sector = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Mainboard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Upcoming')

    # Dates
    open_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    listing_date = models.DateField(null=True, blank=True)

    # Issue Mechanics
    price_band_low = models.FloatField(default=0.0)
    price_band_high = models.FloatField(default=0.0)
    lot_size = models.IntegerField(default=1)
    issue_size_cr = models.FloatField(default=0.0, help_text="Total Issue Size in INR Crores")
    fresh_issue_cr = models.FloatField(default=0.0, help_text="Fresh Issue proceeds retained by company")
    ofs_cr = models.FloatField(default=0.0, help_text="Offer for Sale proceeds cashing out promoters/PE")
    listing_exchange = models.CharField(max_length=50, default='BSE, NSE')

    # Sentiment & Gray Market
    gmp = models.FloatField(default=0.0, help_text="Grey Market Premium in INR")
    gmp_percent = models.FloatField(default=0.0, help_text="GMP as % of upper band")
    qib_subscription = models.FloatField(default=0.0, help_text="Qualified Institutional Buyers multiple")
    nii_subscription = models.FloatField(default=0.0, help_text="Non-Institutional / HNI multiple")
    retail_subscription = models.FloatField(default=0.0, help_text="Retail Individual Investors multiple")
    total_subscription = models.FloatField(default=0.0)

    # Restated Financials & Solvency
    revenue_3y_cagr = models.FloatField(default=0.15)
    pat_3y_cagr = models.FloatField(default=0.20)
    operating_margin = models.FloatField(default=15.0)
    net_margin = models.FloatField(default=10.0)
    pre_roe = models.FloatField(default=16.0)
    pre_roce = models.FloatField(default=18.0)
    debt_to_equity = models.FloatField(default=0.40)
    interest_coverage = models.FloatField(default=8.0)
    fcf_positive = models.BooleanField(default=True)

    # Valuation Multiples vs Listed Peers
    post_pe = models.FloatField(default=25.0, help_text="P/E at upper band based on post-money equity")
    post_pb = models.FloatField(default=3.5)
    industry_pe = models.FloatField(default=30.0, help_text="Median P/E of listed peers in same sector")

    # Shareholding & Objects
    promoter_holding_pre = models.FloatField(default=80.0)
    promoter_holding_post = models.FloatField(default=62.0)
    lead_managers = models.TextField(blank=True, default='')
    anchor_investors = models.TextField(blank=True, default='')
    objects_of_issue = models.TextField(blank=True, default='Organic Capex, Debt Reduction, and General Corporate Purposes')
    drhp_url = models.URLField(max_length=500, blank=True, default='')
    litigation_flag = models.BooleanField(default=False)
    auditor_qualification = models.BooleanField(default=False)

    # Institutional Multi-Factor Synthesis
    composite_score = models.FloatField(default=65.0)
    recommendation = models.CharField(max_length=50, default='Hold / Neutral')
    strategies_json = models.TextField(default='{}', help_text="JSON mapping of all 9 legendary strategy evaluations")
    thesis_invalidations_json = models.TextField(default='[]', help_text="JSON list of 3 explicit thesis failure conditions")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-composite_score', 'open_date']
        verbose_name = "IPO Listing"
        verbose_name_plural = "IPO Listings"

    def save(self, *args, **kwargs):
        """
        Enforces strict mathematical and calendar status integrity:
        - If listing_date <= today: Status is strictly 'Listed'
        - If open_date <= today <= close_date: Status is strictly 'Open'
        - If close_date < today < listing_date: Status is 'Closed'
        - If today < open_date: Status is strictly 'Upcoming'
        """
        from datetime import date
        today = date.today()
        if self.listing_date and today >= self.listing_date:
            self.status = 'Listed'
        elif self.open_date and self.close_date:
            if today < self.open_date:
                self.status = 'Upcoming'
            elif self.open_date <= today <= self.close_date:
                self.status = 'Open'
            elif today > self.close_date:
                if self.listing_date and today < self.listing_date:
                    self.status = 'Closed'
                else:
                    self.status = 'Listed'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name} ({self.symbol}) - ₹{self.price_band_high}"

    @property
    def fresh_ratio_pct(self) -> float:
        """Percentage of issue that is Fresh Capital."""
        if self.issue_size_cr > 0:
            return round((self.fresh_issue_cr / self.issue_size_cr) * 100.0, 1)
        return 50.0

    @property
    def ofs_ratio_pct(self) -> float:
        """Percentage of issue that is Offer for Sale."""
        if self.issue_size_cr > 0:
            return round((self.ofs_cr / self.issue_size_cr) * 100.0, 1)
        return 50.0

    @property
    def estimated_listing_price(self) -> float:
        """Estimated listing price based on current upper band + GMP."""
        return round(self.price_band_high + self.gmp, 2)

    @property
    def minimum_investment(self) -> float:
        """Minimum capital required to apply for 1 retail lot."""
        return round(self.price_band_high * self.lot_size, 2)

    @property
    def strategies(self) -> dict:
        """Decodes the JSON strategies into a Python dictionary."""
        try:
            return json.loads(self.strategies_json)
        except Exception:
            return {}

    @property
    def thesis_invalidations(self) -> list:
        """Decodes the JSON failure conditions into a Python list."""
        try:
            return json.loads(self.thesis_invalidations_json)
        except Exception:
            return []

    @property
    def subscription_dates_display(self) -> str:
        """Exact Chittorgarh subscription date range format: Wed, Jun 25, 2025 - Fri, Jun 27, 2025."""
        if self.open_date and self.close_date:
            return f"{self.open_date.strftime('%a, %b %d, %Y')} - {self.close_date.strftime('%a, %b %d, %Y')}"
        return "TBA"

    @property
    def chittorgarh_summary(self) -> str:
        """
        Exact Chittorgarh listing banner summary:
        e.g., 'Bookbuilding IPO | ₹12,500 Cr | Listed at BSE, NSE | Wed, Jun 25, 2025 - Fri, Jun 27, 2025'
        """
        issue_type = "Bookbuilding IPO" if self.category == "Mainboard" else "SME IPO"
        size_str = f"₹{self.issue_size_cr:,.0f} Cr"
        exchange_str = f"Listed at {self.listing_exchange}" if self.status == 'Listed' else f"Listing at {self.listing_exchange}"
        dates_str = self.subscription_dates_display
        return f"{issue_type} | {size_str} | {exchange_str} | {dates_str}"

    @property
    def is_closing_today(self) -> bool:
        """Returns True if today is the final bidding day for an open IPO."""
        from datetime import date
        return self.status in ['Open', 'Ongoing'] and self.close_date == date.today()

    @property
    def is_bidding_active(self) -> bool:
        """Returns True if the IPO is actively taking bids today."""
        from datetime import date
        today = date.today()
        if self.status in ['Open', 'Ongoing']:
            if self.open_date and self.close_date:
                return self.open_date <= today <= self.close_date
            return True
        return False

    @property
    def bidding_urgency_label(self) -> str:
        """Returns human-friendly bidding timeline status."""
        from datetime import date
        today = date.today()
        if self.status in ['Open', 'Ongoing']:
            if self.close_date == today:
                return "Closes Today (5:00 PM IST)"
            elif self.close_date and self.close_date > today:
                days = (self.close_date - today).days
                return f"Closes in {days} day{'s' if days > 1 else ''}"
            return "Ongoing / Open"
        elif self.status == 'Upcoming':
            if self.open_date:
                days = (self.open_date - today).days
                if days > 0:
                    return f"Opens in {days} days"
                elif days == 0:
                    return "Opens Today"
            return "Upcoming"
        return self.status
