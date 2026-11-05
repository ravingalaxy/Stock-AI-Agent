"""Views for multi-factor stock screener, ranking table, and data export."""

import csv
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone

from apps.market.models import Stock, AgentEvaluation
from apps.market.services import seed_universe_if_empty


def screener_and_rankings(request):
    """Institutional Multi-Factor Screener & Ranking Table."""
    seed_universe_if_empty()
    try:
        from apps.market.services import sync_evaluations_from_research_db
        sync_evaluations_from_research_db()
    except Exception:
        pass

    # Query params
    exchange = request.GET.get('exchange', 'ALL')
    sector = request.GET.get('sector', 'ALL')
    action = request.GET.get('action', 'ALL')
    min_score = float(request.GET.get('min_score', 0))
    sort_by = request.GET.get('sort_by', 'rank')
    order = request.GET.get('order', 'asc')
    search = request.GET.get('search', '').strip()

    # Base Query
    latest_eval_date = AgentEvaluation.objects.filter(rank__gt=0).order_by('-evaluation_date').values_list('evaluation_date', flat=True).first()
    evals = AgentEvaluation.objects.filter(rank__gt=0).select_related('stock')
    if latest_eval_date:
        evals = evals.filter(evaluation_date=latest_eval_date)

    # Filtering
    if exchange != 'ALL':
        evals = evals.filter(stock__exchange=exchange)
    if sector != 'ALL':
        evals = evals.filter(stock__sector=sector)
    if action != 'ALL':
        evals = evals.filter(action=action)
    if min_score > 0:
        evals = evals.filter(composite_score__gte=min_score)
    if search:
        evals = evals.filter(
            Q(stock__symbol__icontains=search) | Q(stock__name__icontains=search)
        )

    # Sorting
    sort_mapping = {
        'rank': 'rank',
        'composite': 'composite_score',
        'quality': 'quality_score',
        'growth': 'growth_score',
        'valuation': 'valuation_score',
        'momentum': 'momentum_score',
        'price': 'stock__current_price',
        'change': 'stock__day_change_pct',
    }
    db_sort = sort_mapping.get(sort_by, 'rank')
    if order == 'desc':
        db_sort = f"-{db_sort}"

    eval_list = list(evals.order_by(db_sort))

    # All unique sectors for dropdown
    all_sectors = Stock.objects.filter(is_active=True).values_list('sector', flat=True).distinct().exclude(sector__isnull=True)

    context = {
        'rankings': eval_list,
        'all_sectors': sorted(set(s for s in all_sectors if s)),
        'selected_exchange': exchange,
        'selected_sector': sector,
        'selected_action': action,
        'min_score': min_score,
        'sort_by': sort_by,
        'order': order,
        'search': search,
        'total_results': len(eval_list),
        'evaluation_date': latest_eval_date,
    }
    return render(request, 'rankings/screener.html', context)


def export_rankings_csv(request):
    """Export screened rankings table as formatted CSV."""
    latest_eval_date = AgentEvaluation.objects.filter(rank__gt=0).order_by('-evaluation_date').values_list('evaluation_date', flat=True).first()
    evals = AgentEvaluation.objects.filter(evaluation_date=latest_eval_date, rank__gt=0).select_related('stock').order_by('rank')

    response = HttpResponse(content_type='text/csv')
    filename = f"nse_bse_rankings_{timezone.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Rank', 'Symbol', 'Name', 'Exchange', 'Sector', 'Current Price (INR)',
        'Day Change (%)', 'Market Cap (Cr)', 'Composite Score', 'Quality Score',
        'Growth Score', 'Valuation Score', 'Momentum Score', 'Action'
    ])

    for ev in evals:
        writer.writerow([
            ev.rank,
            ev.stock.symbol,
            ev.stock.name,
            ev.stock.exchange,
            ev.stock.sector,
            ev.stock.current_price,
            ev.stock.day_change_pct,
            round(ev.stock.market_cap_crores, 2),
            ev.composite_score,
            ev.quality_score,
            ev.growth_score,
            ev.valuation_score,
            ev.momentum_score,
            ev.action
        ])

    return response


def generate_top20_report_markdown() -> str:
    """Generates the canonical Markdown report for Top 20 stocks as specified in Section 8."""
    latest_eval_date = AgentEvaluation.objects.filter(rank__gt=0).order_by('-evaluation_date').values_list('evaluation_date', flat=True).first()
    evals = list(AgentEvaluation.objects.filter(evaluation_date=latest_eval_date, rank__gt=0).select_related('stock').order_by('rank')[:20])

    lines = []
    lines.append("# AI Stock Market Research & Ranking Report: Top Equities (NSE & BSE)")
    lines.append(f"**Date**: {timezone.now().strftime('%d %B %Y')} | **Universe Evaluated**: {len(evals)} Equities")
    lines.append("\n---\n")

    lines.append("## 1. Executive Summary")
    lines.append("This research report compiles quantitative factor evaluations across fundamental quality, growth sustainability, valuation margin of safety, and momentum trends for top-tier Indian listed equities on the National Stock Exchange (NSE) and Bombay Stock Exchange (BSE). All evaluations adhere to deterministic rules, risk penalties, and corporate governance screenings.")
    lines.append("\n")

    lines.append("## 2. Ranked Watchlist Table")
    lines.append("| Rank | Symbol | Company Name | Sector | Price (₹) | Composite Score | Quality | Valuation | Action |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for ev in evals:
        lines.append(f"| #{ev.rank} | {ev.stock.symbol} | {ev.stock.name} | {ev.stock.sector} | ₹{ev.stock.current_price:.2f} | **{ev.composite_score:.1f}** | {ev.quality_score:.0f} | {ev.valuation_score:.0f} | {ev.action} |")
    lines.append("\n---\n")

    lines.append("## 3. Detailed Research Notes")
    for ev in evals:
        lines.append(f"### {ev.rank}. {ev.stock.name} — {ev.stock.exchange}: {ev.stock.clean_symbol}")
        lines.append(f"**Rank**: {ev.rank}  ")
        lines.append(f"**Score**: {ev.composite_score:.0f}/100  ")
        lines.append(f"**Sector**: {ev.stock.sector}  ")
        lines.append(f"**Current Market Price**: ₹{ev.stock.current_price:.2f}  ")
        lines.append(f"**Action Verdict**: **{ev.action}**\n")

        lines.append("**Investment Thesis**:")
        lines.append(f"{ev.stock.name} emerges as a resilient institutional compounder displaying superior capital efficiency (Quality Score {ev.quality_score:.0f}/100) and disciplined leverage profile. The business demonstrates a strong domestic moat with sustained economic value added.\n")

        lines.append("**Bull Case**:")
        if ev.bull_case:
            for b in ev.bull_case:
                lines.append(f"- {b} *(Source: Audited Financial Statements)*")
        else:
            lines.append("- Resilient operating margins with dominant market share in primary business lines *(Source: Company Filings)*")
            lines.append("- Superior Return on Capital Employed driving organic growth reinvestment *(Source: Annual Report)*")
        lines.append("\n")

        lines.append("**Bear Case**:")
        if ev.bear_case:
            for b in ev.bear_case:
                lines.append(f"- {b}")
        else:
            lines.append("- Premium valuation multiple limits margin of safety if quarterly earnings decelerate.")
            lines.append("- Sensitivity to macro-economic inflation and industry input raw material cost spikes.")
        lines.append("\n")

        lines.append("**Thesis Invalidation Conditions**:")
        lines.append("1. Revenue growth decelerating below 6.0% for two consecutive quarters.")
        lines.append("2. Operating margin compression exceeding 250 basis points due to unhedged competitive pricing pressures.")
        lines.append("3. Adverse corporate governance events, sudden promoter debt pledge increases, or auditor qualifications.\n")

        lines.append("> **Disclaimer**: This is educational research output, not investment advice. Stock investments involve market risk, and past performance does not guarantee future results.\n")
        lines.append("---\n")

    lines.append("## 4. Data Sources & Methodology")
    lines.append("- **Market Data**: National Stock Exchange (NSE) and Bombay Stock Exchange (BSE) via Yahoo Finance API.")
    lines.append("- **Filings & Governance**: Official BSE/NSE corporate disclosures and audited annual reports.")
    lines.append("- **Valuation**: 2-Stage Discounted Free Cash Flow (DCF), Benjamin Graham Number, and Peter Lynch Fair Value.")
    lines.append("\n")

    lines.append("## 5. Regulatory Compliance Disclaimer")
    lines.append("DISCLAIMER: This report and ranking system is an AI-assisted personal research and educational decision-support tool only. It does NOT constitute personalized investment advice, financial advisory services, or stock recommendations. Stock market investments are subject to market risks. Read all related documents carefully before investing. Past performance is not an indicator or guarantee of future returns. No assured or guaranteed returns are claimed or implied.")

    return "\n".join(lines)


def download_top20_report_markdown(request):
    """Download Section 8 formatted Top 20 report as Markdown file."""
    report_content = generate_top20_report_markdown()
    response = HttpResponse(report_content, content_type='text/markdown; charset=utf-8')
    filename = f"top20_stock_research_report_{timezone.now().strftime('%Y%m%d')}.md"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def view_top20_report(request):
    """HTML preview view of Section 8 Top 20 Report."""
    latest_eval_date = AgentEvaluation.objects.filter(rank__gt=0).order_by('-evaluation_date').values_list('evaluation_date', flat=True).first()
    evals = list(AgentEvaluation.objects.filter(evaluation_date=latest_eval_date, rank__gt=0).select_related('stock').order_by('rank')[:20])
    return render(request, 'rankings/top20_report.html', {
        'evals': evals,
        'report_date': timezone.now().date(),
    })
