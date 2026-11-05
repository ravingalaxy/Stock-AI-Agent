"""Database models for user portfolio holdings and watchlist."""

from django.db import models


class PortfolioHolding(models.Model):
    """User equity portfolio holding."""
    symbol = models.CharField(max_length=25, unique=True, help_text="e.g. RELIANCE.NS")
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=120, blank=True, default="General")
    quantity = models.IntegerField(default=1)
    buy_price = models.FloatField(help_text="Average purchase price in INR")
    current_price = models.FloatField(help_text="Current market price in INR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-quantity']
        verbose_name = "Portfolio Holding"
        verbose_name_plural = "Portfolio Holdings"

    def __str__(self):
        return f"{self.symbol} ({self.quantity} shares)"

    @property
    def clean_symbol(self) -> str:
        return self.symbol.split('.')[0]

    @property
    def invested_value(self) -> float:
        return self.quantity * self.buy_price

    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def pnl_amount(self) -> float:
        return self.current_value - self.invested_value

    @property
    def pnl_pct(self) -> float:
        if self.invested_value > 0:
            return (self.pnl_amount / self.invested_value) * 100.0
        return 0.0


class WatchlistItem(models.Model):
    """User watchlist stock entry."""
    symbol = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=120, blank=True, default="")
    target_buy_price = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return f"Watchlist: {self.symbol}"


class UploadedPortfolioStatement(models.Model):
    """Uploaded broker statement metadata and executive aggregate KPIs."""
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, default="csv")
    statement_date = models.CharField(max_length=50, default="Not available in uploaded file")
    client_name = models.CharField(max_length=120, default="Not available in uploaded file")
    client_id = models.CharField(max_length=60, default="Not available in uploaded file")
    total_invested = models.FloatField(default=0.0)
    total_current = models.FloatField(default=0.0)
    total_pnl = models.FloatField(default=0.0)
    total_pnl_pct = models.FloatField(default=0.0)
    quality_score = models.FloatField(default=0.0)
    diversification_score = models.FloatField(default=0.0)
    risk_score = models.FloatField(default=0.0)
    research_rating = models.CharField(max_length=120, default="Evaluated Portfolio")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.statement_date}) - {self.client_id}"


class UploadedHoldingRecord(models.Model):
    """Normalized holding extracted from an uploaded portfolio statement."""
    statement = models.ForeignKey(UploadedPortfolioStatement, on_delete=models.CASCADE, related_name='holdings')
    stock_name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=40)
    clean_symbol = models.CharField(max_length=30)
    exchange = models.CharField(max_length=15, default="NSE")
    isin = models.CharField(max_length=30, blank=True, default="Not available in uploaded file")
    quantity = models.FloatField(default=0.0)
    buy_price = models.FloatField(default=0.0)
    current_price = models.FloatField(default=0.0)
    invested_amount = models.FloatField(default=0.0)
    current_value = models.FloatField(default=0.0)
    pnl_amount = models.FloatField(default=0.0)
    pnl_pct = models.FloatField(default=0.0)
    weight_pct = models.FloatField(default=0.0)
    sector = models.CharField(max_length=120, default="Not available in uploaded file")
    market_cap_tier = models.CharField(max_length=50, default="Mid Cap")
    sizing_status = models.CharField(max_length=50, default="Balanced (2-15%)")
    stock_score = models.FloatField(default=50.0)

    class Meta:
        ordering = ['-current_value']

    def __str__(self):
        return f"{self.clean_symbol} in {self.statement.filename}"


class PortfolioAnalysisReport(models.Model):
    """Institutional Expert-Style Review snapshot and 9 Legendary Strategy profile."""
    statement = models.OneToOneField(UploadedPortfolioStatement, on_delete=models.CASCADE, related_name='report')
    dominant_style = models.CharField(max_length=120)
    best_investor_fit = models.CharField(max_length=120)
    analysis_json = models.JSONField(default=dict)
    expert_review_json = models.JSONField(default=dict)
    investor_styles_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.statement.filename}"
