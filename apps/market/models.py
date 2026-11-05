"""Database models for financial markets, stocks, fundamentals, and evaluations."""

from django.db import models
from django.utils import timezone


class Stock(models.Model):
    """Represents an equity traded on NSE or BSE."""
    
    EXCHANGE_CHOICES = [
        ("NSE", "National Stock Exchange (NSE)"),
        ("BSE", "Bombay Stock Exchange (BSE)"),
    ]
    
    symbol = models.CharField(max_length=25, primary_key=True, help_text="e.g. RELIANCE.NS, TCS.NS, 500325.BO")
    name = models.CharField(max_length=255, help_text="Full company legal name")
    isin = models.CharField(max_length=20, blank=True, null=True, help_text="ISIN security identifier")
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES, default="NSE", db_index=True)
    sector = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    industry = models.CharField(max_length=120, blank=True, null=True)
    market_cap = models.FloatField(null=True, blank=True, db_index=True, help_text="Market capitalization in INR")
    current_price = models.FloatField(null=True, blank=True, help_text="Latest market price in INR")
    day_change = models.FloatField(null=True, blank=True, help_text="Daily price change in INR")
    day_change_pct = models.FloatField(null=True, blank=True, help_text="Daily price change percentage")
    pe_ratio = models.FloatField(null=True, blank=True, help_text="Price to Earnings ratio")
    pb_ratio = models.FloatField(null=True, blank=True, help_text="Price to Book ratio")
    dividend_yield = models.FloatField(null=True, blank=True, help_text="Dividend yield percentage")
    description = models.TextField(blank=True, default="")
    website = models.URLField(max_length=300, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['symbol']
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"

    def __str__(self):
        return f"{self.clean_symbol} - {self.name}"

    @property
    def clean_symbol(self) -> str:
        """Returns symbol without exchange suffix."""
        return self.symbol.split(".")[0]

    @property
    def market_cap_crores(self) -> float:
        """Market cap in Crores (1 Cr = 10,000,000 INR)."""
        if self.market_cap:
            return self.market_cap / 10_000_000.0
        return 0.0

    @property
    def formatted_mcap(self) -> str:
        """Formatted string representation of market cap in INR Crores."""
        cr = self.market_cap_crores
        if cr >= 1000:
            return f"₹{cr:,.0f} Cr"
        return f"₹{cr:,.2f} Cr"


class PriceHistory(models.Model):
    """Daily OHLCV historical price record."""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField(db_index=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    adj_close = models.FloatField(null=True, blank=True)
    volume = models.BigIntegerField(default=0)
    sma_20 = models.FloatField(null=True, blank=True)
    sma_50 = models.FloatField(null=True, blank=True)
    sma_200 = models.FloatField(null=True, blank=True)
    rsi_14 = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['stock', 'date'], name='unique_stock_date_price')
        ]
        verbose_name = "Price History"
        verbose_name_plural = "Price Histories"

    def __str__(self):
        return f"{self.stock.symbol} ({self.date}): ₹{self.close:.2f}"


class FundamentalData(models.Model):
    """Financial statement and balance sheet fundamental data."""
    PERIOD_TYPES = [
        ("A", "Annual"),
        ("Q", "Quarterly"),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='fundamentals')
    period_date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=5, choices=PERIOD_TYPES, default="A")
    revenue = models.FloatField(null=True, blank=True)
    net_profit = models.FloatField(null=True, blank=True)
    ebitda = models.FloatField(null=True, blank=True)
    operating_profit = models.FloatField(null=True, blank=True)
    operating_margin = models.FloatField(null=True, blank=True)
    net_margin = models.FloatField(null=True, blank=True)
    roe = models.FloatField(null=True, blank=True, help_text="Return on Equity %")
    roce = models.FloatField(null=True, blank=True, help_text="Return on Capital Employed %")
    debt_to_equity = models.FloatField(null=True, blank=True)
    interest_coverage = models.FloatField(null=True, blank=True)
    fcf = models.FloatField(null=True, blank=True, help_text="Free Cash Flow in INR")
    cfo = models.FloatField(null=True, blank=True, help_text="Cash Flow from Operations")
    promoter_holding_pct = models.FloatField(null=True, blank=True)
    promoter_pledged_pct = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_date']
        constraints = [
            models.UniqueConstraint(fields=['stock', 'period_date', 'period_type'], name='unique_stock_period_fundamentals')
        ]

    def __str__(self):
        return f"{self.stock.symbol} ({self.period_type} {self.period_date})"


class AgentEvaluation(models.Model):
    """Deterministic & AI Agent multi-factor evaluation snapshot."""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='evaluations')
    evaluation_date = models.DateField(default=timezone.now, db_index=True)
    composite_score = models.FloatField(default=0.0, db_index=True)
    quality_score = models.FloatField(default=0.0)
    growth_score = models.FloatField(default=0.0)
    valuation_score = models.FloatField(default=0.0)
    momentum_score = models.FloatField(default=0.0)
    catalyst_score = models.FloatField(default=0.0)
    risk_score = models.FloatField(default=0.0)
    rank = models.IntegerField(default=0, db_index=True)
    action = models.CharField(max_length=25, default="Research") # Strong Buy, Research, Watch, Avoid
    confidence = models.CharField(max_length=20, default="Medium")
    bull_case = models.JSONField(default=list)
    bear_case = models.JSONField(default=list)
    key_catalysts = models.JSONField(default=list)
    risk_flags = models.JSONField(default=list)
    investor_scores = models.JSONField(default=dict)
    probability_metrics = models.JSONField(default=dict)
    dcf_valuation = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rank', '-composite_score']
        constraints = [
            models.UniqueConstraint(fields=['stock', 'evaluation_date'], name='unique_stock_eval_date')
        ]

    def __str__(self):
        return f"#{self.rank} {self.stock.symbol} ({self.composite_score:.1f}/100)"


class BacktestRunRecord(models.Model):
    """Point-in-time quantitative backtest simulation run."""
    run_id = models.CharField(max_length=60, primary_key=True)
    strategy_name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    rebalance_frequency = models.CharField(max_length=15, default="M")
    initial_capital = models.FloatField(default=1000000.0)
    final_capital = models.FloatField()
    cagr = models.FloatField()
    volatility = models.FloatField()
    sharpe_ratio = models.FloatField()
    max_drawdown = models.FloatField()
    win_rate = models.FloatField()
    benchmark_cagr = models.FloatField()
    alpha = models.FloatField()
    beta = models.FloatField()
    equity_curve = models.JSONField(default=list)
    trades = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.strategy_name} ({self.run_id}): CAGR {self.cagr*100:.1f}%"
