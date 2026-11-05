"""Views for Portfolio Management, Holdings, Position Sizing & Risk Controls."""

import json
from typing import Optional, List, Dict, Any, Union
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import PortfolioHolding, WatchlistItem
from apps.market.models import Stock
from src.analysis.portfolio_manager import PortfolioManager, HoldingItem, get_sample_holdings


def seed_portfolio_if_empty():
    """Seeds sample portfolio holdings if table is empty."""
    if PortfolioHolding.objects.count() > 0:
        return

    sample = get_sample_holdings()
    with transaction.atomic():
        for item in sample:
            # Sync latest price if available from Stock model
            stock = Stock.objects.filter(symbol=item.symbol).first()
            curr = stock.current_price if stock and stock.current_price else item.current_price
            PortfolioHolding.objects.create(
                symbol=item.symbol,
                name=item.company_name,
                sector=item.sector,
                quantity=item.quantity,
                buy_price=item.buy_price,
                current_price=curr
            )


def portfolio_dashboard(request):
    """Institutional Portfolio Management Dashboard with dynamic market pricing."""
    seed_portfolio_if_empty()

    # Query all active holdings and synchronize current prices from Stock model
    holdings_db = list(PortfolioHolding.objects.all())
    for h in holdings_db:
        stk = Stock.objects.filter(symbol=h.symbol).first()
        if stk and stk.current_price and stk.current_price > 0:
            if abs(h.current_price - stk.current_price) > 0.01:
                h.current_price = stk.current_price
                h.save(update_fields=['current_price', 'updated_at'])

    holding_items = [
        HoldingItem(
            symbol=h.symbol,
            company_name=h.name,
            sector=h.sector,
            quantity=h.quantity,
            buy_price=h.buy_price,
            current_price=h.current_price
        )
        for h in holdings_db
    ]

    pm = PortfolioManager(max_single_stock_pct=20.0, max_sector_pct=30.0)
    eval_result = pm.evaluate_portfolio(holding_items)

    # Sector chart data for Chart.js
    sector_labels = list(eval_result['sector_allocation'].keys())
    sector_weights = [v['weight_pct'] for v in eval_result['sector_allocation'].values()]
    sector_values = [v['value'] for v in eval_result['sector_allocation'].values()]

    context = {
        'total_invested': eval_result['total_invested'],
        'total_current': eval_result['total_current'],
        'total_pnl': eval_result['total_pnl'],
        'total_pnl_pct': eval_result['total_pnl_pct'],
        'holdings': eval_result['holdings_summary'],
        'holdings_count': eval_result['holdings_count'],
        'sector_allocation': eval_result['sector_allocation'],
        'sector_labels_json': json.dumps(sector_labels),
        'sector_weights_json': json.dumps(sector_weights),
        'sector_values_json': json.dumps(sector_values),
        'alerts': eval_result['alerts'],
        'rebalancing_suggestions': eval_result['rebalancing_suggestions'],
    }
    return render(request, 'portfolio/portfolio.html', context)


@require_http_methods(["POST"])
def calculate_position_size_api(request):
    """Dynamic AJAX position sizing calculator."""
    try:
        data = json.loads(request.body)
        capital = float(data.get('capital', 1000000.0))
        entry_price = float(data.get('entry_price', 1000.0))
        risk_profile = data.get('risk_profile', 'conservative')
        stop_loss = float(data.get('stop_loss', 0.0)) if data.get('stop_loss') else None

        res = PortfolioManager.calculate_position_size(
            portfolio_capital=capital,
            risk_profile=risk_profile,
            entry_price=entry_price,
            stop_loss_price=stop_loss
        )
        return JsonResponse(res)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
def calculate_stop_loss_api(request):
    """Dynamic AJAX stop-loss and target price calculator."""
    try:
        data = json.loads(request.body)
        entry_price = float(data.get('entry_price', 1000.0))
        sl_pct = float(data.get('stop_loss_pct', 6.0))
        rr_ratio = float(data.get('risk_reward_ratio', 2.0))

        res = PortfolioManager.calculate_stop_loss_and_target(
            entry_price=entry_price,
            risk_reward_ratio=rr_ratio,
            stop_loss_pct=sl_pct
        )
        return JsonResponse(res)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def sync_portfolio_prices_api(request):
    """Synchronizes real-time quotes for all portfolio holdings and returns updated P&L."""
    holdings = list(PortfolioHolding.objects.all())
    symbols = [h.symbol for h in holdings]
    if symbols:
        from apps.market.services import sync_live_market_data
        sync_live_market_data(symbols=symbols, limit=len(symbols))

    # Re-sync updated prices
    for h in holdings:
        stk = Stock.objects.filter(symbol=h.symbol).first()
        if stk and stk.current_price:
            h.current_price = stk.current_price
            h.save(update_fields=['current_price', 'updated_at'])

    holding_items = [
        HoldingItem(h.symbol, h.name, h.sector, h.quantity, h.buy_price, h.current_price)
        for h in PortfolioHolding.objects.all()
    ]
    pm = PortfolioManager(max_single_stock_pct=20.0, max_sector_pct=30.0)
    res = pm.evaluate_portfolio(holding_items)
    return JsonResponse(res)


# =========================================================================
# PORTFOLIO ANALYSIS & EXPERT-STYLE EVALUATION
# =========================================================================

from pathlib import Path
from .models import UploadedPortfolioStatement, UploadedHoldingRecord, PortfolioAnalysisReport
from src.portfolio.portfolio_parser import PortfolioParser, ParsedPortfolio, ParsedHolding
from src.portfolio.portfolio_analyzer import PortfolioAnalyzer, PortfolioMetrics
from src.portfolio.investor_styles import PortfolioInvestorStyles, PortfolioStyleProfile
from src.portfolio.portfolio_report import PortfolioReportGenerator, ExpertPortfolioReview, COMPLIANCE_DISCLAIMER
from src.portfolio.top_portfolios import TopPortfoliosRepository, TopMarketPortfolio, TopPortfolioHolding


def seed_fyers_statement_if_empty() -> Optional[UploadedPortfolioStatement]:
    """Auto-seeds FYERS statement from workspace if no uploaded statement exists."""
    if UploadedPortfolioStatement.objects.exists():
        return UploadedPortfolioStatement.objects.first()

    sample_candidates = [
        Path("sample_portfolio_statement.csv"),
        Path(__file__).resolve().parent.parent.parent / "sample_portfolio_statement.csv",
        Path("FYERS_holding_statements_XR45621_2026-10-23.csv"),
        Path(__file__).resolve().parent.parent.parent / "FYERS_holding_statements_XR45621_2026-10-23.csv"
    ]
    sample_path = next((p for p in sample_candidates if p.exists()), Path("sample_portfolio_statement.csv"))
    parsed = None

    if sample_path.exists():
        try:
            parsed = PortfolioParser.parse_file(sample_path)
        except Exception:
            parsed = None

    if not parsed or not parsed.is_valid:
        parsed = TopPortfoliosRepository.get_all_portfolios()[0].to_parsed_portfolio()

    try:

        metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
        style_profile = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)
        review = ExpertPortfolioReview(metrics, style_profile).generate_review()

        with transaction.atomic():
            stmt = UploadedPortfolioStatement.objects.create(
                filename=parsed.filename,
                file_type=parsed.file_type,
                statement_date=parsed.statement_date,
                client_name=parsed.client_name,
                client_id=parsed.client_id,
                total_invested=metrics.total_invested,
                total_current=metrics.total_current,
                total_pnl=metrics.total_pnl,
                total_pnl_pct=metrics.total_pnl_pct,
                quality_score=metrics.portfolio_quality_score,
                diversification_score=metrics.portfolio_diversification_score,
                risk_score=metrics.portfolio_risk_score,
                research_rating=metrics.portfolio_research_rating
            )

            for h in metrics.holdings_analysis:
                UploadedHoldingRecord.objects.create(
                    statement=stmt,
                    stock_name=h.stock_name,
                    symbol=h.symbol,
                    clean_symbol=h.clean_symbol,
                    exchange=h.exchange,
                    isin=h.isin,
                    quantity=h.quantity,
                    buy_price=h.buy_price,
                    current_price=h.current_price,
                    invested_amount=h.invested_amount,
                    current_value=h.current_value,
                    pnl_amount=h.pnl_amount,
                    pnl_pct=h.pnl_pct,
                    weight_pct=h.weight_pct,
                    sector=h.sector,
                    market_cap_tier=h.market_cap_tier,
                    sizing_status=h.sizing_status,
                    stock_score=h.stock_score
                )

            PortfolioAnalysisReport.objects.create(
                statement=stmt,
                dominant_style=style_profile.dominant_style,
                best_investor_fit=style_profile.best_matching_investor,
                analysis_json={
                    "sector_allocation": metrics.sector_allocation,
                    "market_cap_allocation": metrics.market_cap_allocation,
                    "top_5_holdings": metrics.top_5_holdings,
                    "top_5_weight_pct": metrics.top_5_weight_pct,
                    "excessive_concentration": metrics.excessive_concentration_stocks,
                    "overlapping_exposures": metrics.overlapping_exposures,
                    "best_performers": metrics.best_performers,
                    "worst_performers": metrics.worst_performers
                },
                expert_review_json=review,
                investor_styles_json={
                    "average_scores": style_profile.average_scores,
                    "strategy_fits": style_profile.strategy_fits,
                    "conflicting_holdings": style_profile.conflicting_holdings,
                    "portfolio_orientation_summary": style_profile.portfolio_orientation_summary
                }
            )
            return stmt
    except Exception as e:
        print(f"Error seeding FYERS statement: {e}")
        return None


def portfolio_analysis_view(request):
    """
    Comprehensive Portfolio Analysis and Expert-Style Evaluation Dashboard.
    Supports CSV, XLSX, XLS, PDF, DOCX file uploads, interactive Chart.js visualizations,
    9 Legendary Investor scoring, and multi-format report exports.
    """
    error_msg = None
    success_msg = None

    if request.method == "POST":
        uploaded_file = request.FILES.get("portfolio_file")
        if not uploaded_file:
            error_msg = "Please choose a file to upload (CSV, XLSX, XLS, PDF, or DOCX)."
        else:
            try:
                content = uploaded_file.read()
                filename = uploaded_file.name

                # Parse file
                parsed = PortfolioParser.parse_file(content, filename=filename)

                if not parsed.is_valid:
                    error_msg = "; ".join(parsed.errors) or "Failed to extract valid holdings from file."
                else:
                    metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
                    style_profile = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)
                    review = ExpertPortfolioReview(metrics, style_profile).generate_review()

                    with transaction.atomic():
                        stmt = UploadedPortfolioStatement.objects.create(
                            filename=parsed.filename,
                            file_type=parsed.file_type,
                            statement_date=parsed.statement_date,
                            client_name=parsed.client_name,
                            client_id=parsed.client_id,
                            total_invested=metrics.total_invested,
                            total_current=metrics.total_current,
                            total_pnl=metrics.total_pnl,
                            total_pnl_pct=metrics.total_pnl_pct,
                            quality_score=metrics.portfolio_quality_score,
                            diversification_score=metrics.portfolio_diversification_score,
                            risk_score=metrics.portfolio_risk_score,
                            research_rating=metrics.portfolio_research_rating
                        )

                        for h in metrics.holdings_analysis:
                            UploadedHoldingRecord.objects.create(
                                statement=stmt,
                                stock_name=h.stock_name,
                                symbol=h.symbol,
                                clean_symbol=h.clean_symbol,
                                exchange=h.exchange,
                                isin=h.isin,
                                quantity=h.quantity,
                                buy_price=h.buy_price,
                                current_price=h.current_price,
                                invested_amount=h.invested_amount,
                                current_value=h.current_value,
                                pnl_amount=h.pnl_amount,
                                pnl_pct=h.pnl_pct,
                                weight_pct=h.weight_pct,
                                sector=h.sector,
                                market_cap_tier=h.market_cap_tier,
                                sizing_status=h.sizing_status,
                                stock_score=h.stock_score
                            )

                        PortfolioAnalysisReport.objects.create(
                            statement=stmt,
                            dominant_style=style_profile.dominant_style,
                            best_investor_fit=style_profile.best_matching_investor,
                            analysis_json={
                                "sector_allocation": metrics.sector_allocation,
                                "market_cap_allocation": metrics.market_cap_allocation,
                                "top_5_holdings": metrics.top_5_holdings,
                                "top_5_weight_pct": metrics.top_5_weight_pct,
                                "excessive_concentration": metrics.excessive_concentration_stocks,
                                "overlapping_exposures": metrics.overlapping_exposures,
                                "best_performers": metrics.best_performers,
                                "worst_performers": metrics.worst_performers
                            },
                            expert_review_json=review,
                            investor_styles_json={
                                "average_scores": style_profile.average_scores,
                                "strategy_fits": style_profile.strategy_fits,
                                "conflicting_holdings": style_profile.conflicting_holdings,
                                "portfolio_orientation_summary": style_profile.portfolio_orientation_summary
                            }
                        )
                        return redirect(f"/portfolio/analysis/?statement_id={stmt.id}")
            except Exception as e:
                error_msg = f"Error processing portfolio statement: {str(e)}"

    # Determine which statement to display
    cleared = request.GET.get("cleared") == "1"
    if request.GET.get("reset") == "success":
        success_msg = "Portfolio has been reset to default sample statement (FYERS)."
    elif cleared:
        success_msg = "Portfolio statements have been cleared. Upload a new statement to begin analysis, or click 'Reset to Default'."

    statement_id = request.GET.get("statement_id")
    active_stmt = None
    if statement_id:
        active_stmt = UploadedPortfolioStatement.objects.filter(id=statement_id).first()

    if not active_stmt and not cleared:
        active_stmt = seed_fyers_statement_if_empty()

    recent_statements = UploadedPortfolioStatement.objects.all().order_by("-uploaded_at")[:8]

    # Re-evaluate live metrics and style profile for active statement
    metrics = None
    style_profile = None
    review = None

    if active_stmt:
        # Convert DB records to ParsedPortfolio
        db_holdings = active_stmt.holdings.all()
        parsed_holdings = [
            ParsedHolding(
                stock_name=h.stock_name,
                symbol=h.symbol,
                clean_symbol=h.clean_symbol,
                exchange=h.exchange,
                isin=h.isin,
                quantity=h.quantity,
                buy_price=h.buy_price,
                current_price=h.current_price,
                invested_amount=h.invested_amount,
                current_value=h.current_value,
                pnl_amount=h.pnl_amount,
                pnl_pct=h.pnl_pct,
                sector=h.sector
            )
            for h in db_holdings
        ]
        parsed = ParsedPortfolio(
            filename=active_stmt.filename,
            file_type=active_stmt.file_type,
            statement_date=active_stmt.statement_date,
            client_name=active_stmt.client_name,
            client_id=active_stmt.client_id,
            reported_invested=active_stmt.total_invested,
            reported_current=active_stmt.total_current,
            reported_pnl=active_stmt.total_pnl,
            holdings=parsed_holdings
        )
        metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
        style_profile = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)
        review = ExpertPortfolioReview(metrics, style_profile).generate_review()

    # Prepare chart data
    sector_labels = list(metrics.sector_allocation.keys()) if metrics else []
    sector_weights = [d["weight_pct"] for d in metrics.sector_allocation.values()] if metrics else []
    sector_values = [d["value"] for d in metrics.sector_allocation.values()] if metrics else []

    top_stock_labels = [h.clean_symbol for h in (metrics.holdings_analysis[:10] if metrics else [])]
    top_stock_weights = [h.weight_pct for h in (metrics.holdings_analysis[:10] if metrics else [])]

    mcap_labels = list(metrics.market_cap_allocation.keys()) if metrics else []
    mcap_weights = [d["weight_pct"] for d in metrics.market_cap_allocation.values()] if metrics else []

    strategy_names = PortfolioInvestorStyles.STRATEGIES
    strategy_scores = [style_profile.average_scores.get(s, 50.0) for s in strategy_names] if style_profile else []

    # Forensic co-investment relationship with Dalal Street's Top 10 Portfolios
    superinvestor_overlap = TopPortfoliosRepository.calculate_portfolio_overlap(metrics.holdings_analysis) if metrics else None

    context = {
        "superinvestor_overlap": superinvestor_overlap,
        "statement": active_stmt,
        "recent_statements": recent_statements,
        "metrics": metrics,
        "style_profile": style_profile,
        "review": review,
        "error_msg": error_msg,
        "success_msg": success_msg,
        "disclaimer": COMPLIANCE_DISCLAIMER,
        "sector_labels_json": json.dumps(sector_labels),
        "sector_weights_json": json.dumps(sector_weights),
        "sector_values_json": json.dumps(sector_values),
        "stock_labels_json": json.dumps(top_stock_labels),
        "stock_weights_json": json.dumps(top_stock_weights),
        "mcap_labels_json": json.dumps(mcap_labels),
        "mcap_weights_json": json.dumps(mcap_weights),
        "strategy_names_json": json.dumps(strategy_names),
        "strategy_scores_json": json.dumps(strategy_scores),
    }
    return render(request, "portfolio/portfolio_analysis.html", context)


@require_http_methods(["GET", "POST"])
def portfolio_reset_view(request):
    """
    Resets the portfolio analysis module:
    - mode=clear: Clears all uploaded portfolio statements & cached reports, giving a clean slate.
    - mode=default: Clears custom statements and re-seeds the standard FYERS holding statement.
    """
    mode = request.GET.get("mode", request.POST.get("mode", "default"))
    try:
        with transaction.atomic():
            UploadedPortfolioStatement.objects.all().delete()

        if mode == "clear":
            return redirect(f"{reverse('portfolio:analysis')}?cleared=1")
        else:
            seed_fyers_statement_if_empty()
            return redirect(f"{reverse('portfolio:analysis')}?reset=success")
    except Exception as e:
        return redirect(f"{reverse('portfolio:analysis')}?error={str(e)}")


@require_http_methods(["POST"])
def portfolio_preview_api(request):
    """AJAX endpoint for instant preview & column detection of uploaded portfolio file."""
    uploaded_file = request.FILES.get("portfolio_file")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    try:
        content = uploaded_file.read()
        parsed = PortfolioParser.parse_file(content, filename=uploaded_file.name)
        preview_holdings = [h.to_dict() for h in parsed.holdings[:6]]

        return JsonResponse({
            "status": "success",
            "filename": parsed.filename,
            "file_type": parsed.file_type,
            "statement_date": parsed.statement_date,
            "client_name": parsed.client_name,
            "client_id": parsed.client_id,
            "total_invested": parsed.total_invested_calculated,
            "total_current": parsed.total_current_calculated,
            "holdings_count": len(parsed.holdings),
            "raw_headers": parsed.raw_headers,
            "detected_columns": parsed.detected_column_map,
            "preview_holdings": preview_holdings,
            "warnings": parsed.warnings,
            "errors": parsed.errors
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def portfolio_export_report_view(request, fmt: str):
    """Exports portfolio research report in Markdown, CSV, Excel, or PDF."""
    statement_id = request.GET.get("statement_id")
    stmt = None
    if statement_id:
        stmt = UploadedPortfolioStatement.objects.filter(id=statement_id).first()
    if not stmt:
        stmt = UploadedPortfolioStatement.objects.first()

    if not stmt:
        return HttpResponse("No statement available for export.", status=404)

    # Reconstruct metrics & styles
    db_holdings = stmt.holdings.all()
    parsed_holdings = [
        ParsedHolding(
            stock_name=h.stock_name,
            symbol=h.symbol,
            clean_symbol=h.clean_symbol,
            exchange=h.exchange,
            isin=h.isin,
            quantity=h.quantity,
            buy_price=h.buy_price,
            current_price=h.current_price,
            invested_amount=h.invested_amount,
            current_value=h.current_value,
            pnl_amount=h.pnl_amount,
            pnl_pct=h.pnl_pct,
            sector=h.sector
        )
        for h in db_holdings
    ]
    parsed = ParsedPortfolio(
        filename=stmt.filename,
        file_type=stmt.file_type,
        statement_date=stmt.statement_date,
        client_name=stmt.client_name,
        client_id=stmt.client_id,
        reported_invested=stmt.total_invested,
        reported_current=stmt.total_current,
        reported_pnl=stmt.total_pnl,
        holdings=parsed_holdings
    )
    metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
    styles = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)

    fmt_clean = fmt.lower().strip()
    safe_name = Path(stmt.filename).stem

    if fmt_clean == "md" or fmt_clean == "markdown":
        md_text = PortfolioReportGenerator.generate_markdown(metrics, styles)
        response = HttpResponse(md_text, content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="Portfolio_Research_Report_{safe_name}.md"'
        return response

    elif fmt_clean == "csv":
        csv_text = PortfolioReportGenerator.generate_csv(metrics)
        response = HttpResponse(csv_text, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="Portfolio_Holdings_{safe_name}.csv"'
        return response

    elif fmt_clean in ["xlsx", "excel"]:
        excel_bytes = PortfolioReportGenerator.generate_excel(metrics, styles)
        response = HttpResponse(excel_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="Portfolio_Analysis_{safe_name}.xlsx"'
        return response

    elif fmt_clean == "pdf":
        pdf_bytes = PortfolioReportGenerator.generate_pdf(metrics, styles)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Portfolio_Research_Report_{safe_name}.pdf"'
        return response

    return HttpResponse(f"Unsupported format '{fmt}'. Choose md, csv, xlsx, or pdf.", status=400)


def top_portfolios_view(request, portfolio_id=None):
    """
    Top Ten Stock Market Portfolios & Comprehensive Stock-Level Rationales.
    Allows users to explore Dalal Street's top 10 legendary and institutional portfolios,
    inspect the core fundamental rationale for each stock, and run deep 9-investor diagnostics.
    """
    all_portfolios = TopPortfoliosRepository.get_all_portfolios()

    # Search functionality
    query = request.GET.get("q", "").strip()
    search_results = []
    market_stock_match = None

    if query:
        search_results = TopPortfoliosRepository.find_stock_across_portfolios(query)
        if not search_results:
            # Check if this query is a valid listed stock in the broader market
            from apps.market.services import ensure_stock_exists
            stk = ensure_stock_exists(query)
            if stk:
                market_stock_match = stk

    # Determine selected portfolio
    target_id = portfolio_id or request.GET.get("portfolio")
    active_portfolio = None
    if target_id:
        active_portfolio = TopPortfoliosRepository.get_portfolio_by_id(target_id)

    if not active_portfolio:
        active_portfolio = all_portfolios[0]  # Default to Rakesh Jhunjhunwala

    # Prepare chart data
    sec_labels = list(active_portfolio.sector_allocation.keys())
    sec_weights = list(active_portfolio.sector_allocation.values())

    mcap_labels = list(active_portfolio.market_cap_allocation.keys())
    mcap_weights = list(active_portfolio.market_cap_allocation.values())

    stock_labels = [h.clean_symbol for h in active_portfolio.holdings]
    stock_weights = [h.weight_pct for h in active_portfolio.holdings]

    # Check co-investment overlap with the user's active uploaded portfolio
    active_stmt = UploadedPortfolioStatement.objects.order_by("-uploaded_at").first()
    user_overlap_map = {}
    if active_stmt:
        for uh in active_stmt.holdings.all():
            user_overlap_map[uh.clean_symbol.upper()] = {
                "quantity": uh.quantity,
                "current_value": uh.current_value,
                "weight_pct": uh.weight_pct,
                "pnl_pct": uh.pnl_pct,
            }

    user_shared_stocks = []
    user_shared_weight = 0.0
    for h in active_portfolio.holdings:
        match = user_overlap_map.get(h.clean_symbol.upper())
        setattr(h, "user_match", match)
        if match:
            user_shared_stocks.append(h.clean_symbol)
            user_shared_weight += match["weight_pct"]

    context = {
        "all_portfolios": all_portfolios,
        "active_portfolio": active_portfolio,
        "query": query,
        "search_results": search_results,
        "market_stock_match": market_stock_match,
        "active_stmt": active_stmt,
        "user_shared_stocks": user_shared_stocks,
        "user_shared_weight": round(user_shared_weight, 2),
        "disclaimer": COMPLIANCE_DISCLAIMER,
        "sec_labels_json": json.dumps(sec_labels),
        "sec_weights_json": json.dumps(sec_weights),
        "mcap_labels_json": json.dumps(mcap_labels),
        "mcap_weights_json": json.dumps(mcap_weights),
        "stock_labels_json": json.dumps(stock_labels),
        "stock_weights_json": json.dumps(stock_weights),
    }
    return render(request, "portfolio/top_portfolios.html", context)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def sync_top_portfolio_prices_api(request, portfolio_id: str):
    """Synchronizes live quotes from exchange for all holdings in a Top 10 Portfolio."""
    portfolio = TopPortfoliosRepository.get_portfolio_by_id(portfolio_id, sync_prices=False)
    if not portfolio:
        return JsonResponse({"error": "Portfolio not found"}, status=404)

    symbols_to_sync = [f"{h.clean_symbol}.NS" for h in portfolio.holdings]
    try:
        from apps.market.services import sync_live_market_data
        sync_live_market_data(symbols=symbols_to_sync, limit=len(symbols_to_sync))
    except Exception as e:
        print(f"Warning syncing live market data: {e}")

    # Re-fetch with synced live prices
    updated_p = TopPortfoliosRepository.get_portfolio_by_id(portfolio_id, sync_prices=True)
    holdings_data = [
        {"symbol": h.clean_symbol, "name": h.stock_name, "price": h.current_price, "weight": h.weight_pct}
        for h in updated_p.holdings
    ]
    return JsonResponse({
        "status": "success",
        "message": f"Synchronized live market quotes for {portfolio.name}.",
        "portfolio_id": portfolio_id,
        "holdings": holdings_data,
        "updated_count": len(holdings_data)
    })


def load_top_portfolio_into_analysis(request, portfolio_id):
    """
    Converts a Top Market Portfolio into an active UploadedPortfolioStatement
    and redirects directly into the comprehensive 9-investor Portfolio Analysis dashboard.
    """
    portfolio = TopPortfoliosRepository.get_portfolio_by_id(portfolio_id)
    if not portfolio:
        return redirect(reverse("portfolio:top_portfolios"))

    try:
        parsed = portfolio.to_parsed_portfolio()
        metrics = PortfolioAnalyzer.analyze_portfolio(parsed)
        style_profile = PortfolioInvestorStyles.analyze_portfolio_styles(metrics)
        review = ExpertPortfolioReview(metrics, style_profile).generate_review()

        with transaction.atomic():
            stmt = UploadedPortfolioStatement.objects.create(
                filename=f"{portfolio.name} (Top Portfolio).csv",
                file_type="model_portfolio",
                statement_date="25-10-2026",
                client_name=portfolio.manager_or_style,
                client_id=f"TOP-{portfolio.id.upper()}",
                total_invested=metrics.total_invested,
                total_current=metrics.total_current,
                total_pnl=metrics.total_pnl,
                total_pnl_pct=metrics.total_pnl_pct,
                quality_score=metrics.portfolio_quality_score,
                diversification_score=metrics.portfolio_diversification_score,
                risk_score=metrics.portfolio_risk_score,
                research_rating=f"Top Portfolio: {portfolio.name}"
            )

            for h in metrics.holdings_analysis:
                UploadedHoldingRecord.objects.create(
                    statement=stmt,
                    stock_name=h.stock_name,
                    symbol=h.symbol,
                    clean_symbol=h.clean_symbol,
                    exchange=h.exchange,
                    isin=h.isin,
                    quantity=h.quantity,
                    buy_price=h.buy_price,
                    current_price=h.current_price,
                    invested_amount=h.invested_amount,
                    current_value=h.current_value,
                    pnl_amount=h.pnl_amount,
                    pnl_pct=h.pnl_pct,
                    weight_pct=h.weight_pct,
                    sector=h.sector,
                    market_cap_tier=h.market_cap_tier,
                    sizing_status=h.sizing_status,
                    stock_score=h.stock_score
                )

            PortfolioAnalysisReport.objects.create(
                statement=stmt,
                dominant_style=style_profile.dominant_style,
                best_investor_fit=style_profile.best_matching_investor,
                analysis_json={
                    "sector_allocation": metrics.sector_allocation,
                    "market_cap_allocation": metrics.market_cap_allocation,
                    "top_5_holdings": metrics.top_5_holdings,
                    "top_5_weight_pct": metrics.top_5_weight_pct,
                    "excessive_concentration": metrics.excessive_concentration_stocks,
                    "overlapping_exposures": metrics.overlapping_exposures,
                    "best_performers": metrics.best_performers,
                    "worst_performers": metrics.worst_performers
                },
                expert_review_json=review,
                investor_styles_json={
                    "average_scores": style_profile.average_scores,
                    "strategy_fits": style_profile.strategy_fits,
                    "conflicting_holdings": style_profile.conflicting_holdings,
                    "portfolio_orientation_summary": style_profile.portfolio_orientation_summary
                }
            )

        return redirect(f"{reverse('portfolio:analysis')}?statement_id={stmt.id}")
    except Exception as e:
        print(f"Error loading top portfolio into analysis: {e}")
        return redirect(reverse("portfolio:top_portfolios"))


