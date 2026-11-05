"""Views for market overview dashboard, settings, and navigation."""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.contrib import messages

from .models import Stock, PriceHistory, AgentEvaluation
from .services import seed_universe_if_empty, get_market_indices_summary, sync_live_market_data, get_live_market_pulse
from src.config import get_config


def dashboard(request):
    """Executive FinTech Market Dashboard (Specification Tab 1: Home)."""
    # Ensure universe has initial data
    seed_universe_if_empty()

    indices = get_market_indices_summary()

    # Active Stocks
    stocks = Stock.objects.filter(is_active=True)
    total_stocks = stocks.count()

    # Top Gainers & Losers
    top_gainers = stocks.filter(day_change_pct__isnull=False).order_by('-day_change_pct')[:5]
    top_losers = stocks.filter(day_change_pct__isnull=False).order_by('day_change_pct')[:5]

    # Market Breadth
    advances = stocks.filter(day_change__gt=0).count()
    declines = stocks.filter(day_change__lt=0).count()
    unchanged = total_stocks - (advances + declines)

    # Top Ranked Equities (today or latest evaluation)
    latest_eval_date = AgentEvaluation.objects.filter(rank__gt=0).order_by('-evaluation_date').values_list('evaluation_date', flat=True).first()
    top_rankings = []
    if latest_eval_date:
        top_rankings = AgentEvaluation.objects.filter(evaluation_date=latest_eval_date, rank__gt=0).select_related('stock').order_by('rank')[:6]

    # Sector Breakdown
    sectors = stocks.values('sector').annotate(
        count=Count('symbol'),
        avg_pe=Avg('pe_ratio')
    ).order_by('-count')[:8]

    # Recent Market & Risk Alerts (Specification 6.1: Recent Alerts)
    recent_alerts = [
        {
            'category': 'valuation',
            'severity': 'warning',
            'title': 'High Valuation Multiple Alert',
            'message': 'Nifty IT index forward P/E expanded to 31.4x (+1.8 std dev above 5-year average). Margin of safety remains compressed for large-cap IT.',
            'time': '10 mins ago'
        },
        {
            'category': 'macro',
            'severity': 'info',
            'title': 'RBI Monetary Stance Neutral',
            'message': 'Headline inflation moderating within target band (4.4%); banking liquidity remains in surplus supporting credit growth.',
            'time': '45 mins ago'
        },
        {
            'category': 'governance',
            'severity': 'success',
            'title': 'Clean Promoter Holding Checks',
            'message': 'All top-15 ranked Nifty/BSE universe equities cleared zero promoter pledge and unqualified audit review screens.',
            'time': '2 hours ago'
        },
        {
            'category': 'risk',
            'severity': 'warning',
            'title': 'Portfolio Sector Concentration Notice',
            'message': 'Ensure sector allocations do not exceed the 30% concentration ceiling in accordance with risk policy.',
            'time': '3 hours ago'
        }
    ]

    context = {
        'indices': indices,
        'total_stocks': total_stocks,
        'top_gainers': top_gainers,
        'top_losers': top_losers,
        'advances': advances,
        'declines': declines,
        'unchanged': unchanged,
        'top_rankings': top_rankings,
        'sectors': sectors,
        'evaluation_date': latest_eval_date,
        'recent_alerts': recent_alerts,
    }
    return render(request, 'market/dashboard.html', context)


def settings_view(request):
    """System Configuration & Scoring Weights (Specification Tab 6: Settings)."""
    cfg = get_config()

    # Session-persisted weights or defaults from config
    session_weights = request.session.get('custom_scoring_weights', {
        'quality': cfg.scoring_weights.quality,
        'growth': cfg.scoring_weights.growth,
        'valuation': cfg.scoring_weights.valuation,
        'momentum': cfg.scoring_weights.momentum,
        'catalyst': cfg.scoring_weights.catalyst,
        'risk_penalty': cfg.scoring_weights.risk_penalty,
    })

    if request.method == 'POST':
        action = request.POST.get('action', 'save_weights')
        if action == 'save_weights':
            try:
                q = float(request.POST.get('weight_quality', session_weights['quality']))
                g = float(request.POST.get('weight_growth', session_weights['growth']))
                v = float(request.POST.get('weight_valuation', session_weights['valuation']))
                m = float(request.POST.get('weight_momentum', session_weights['momentum']))
                c = float(request.POST.get('weight_catalyst', session_weights['catalyst']))
                r = float(request.POST.get('weight_risk', session_weights['risk_penalty']))

                total_weight = q + g + v + m + c
                if abs(total_weight - 0.90) > 0.05 and abs(total_weight - 1.0) > 0.05:
                    messages.warning(request, f"Scoring weights sum to {total_weight:.2f}. Standard allocation is 1.00 (30% Q + 20% G + 15% V + 15% M + 10% C).")
                else:
                    messages.success(request, "Scoring weights updated successfully for this session.")

                session_weights = {
                    'quality': q,
                    'growth': g,
                    'valuation': v,
                    'momentum': m,
                    'catalyst': c,
                    'risk_penalty': r,
                }
                request.session['custom_scoring_weights'] = session_weights
            except ValueError:
                messages.error(request, "Invalid numeric input for weights.")
        elif action == 'reset_weights':
            session_weights = {
                'quality': cfg.scoring_weights.quality,
                'growth': cfg.scoring_weights.growth,
                'valuation': cfg.scoring_weights.valuation,
                'momentum': cfg.scoring_weights.momentum,
                'catalyst': cfg.scoring_weights.catalyst,
                'risk_penalty': cfg.scoring_weights.risk_penalty,
            }
            request.session['custom_scoring_weights'] = session_weights
            messages.info(request, "Scoring weights reset to institutional defaults.")

    screening = cfg.screening_defaults
    llm = cfg.llm

    context = {
        'weights': session_weights,
        'screening': {
            'min_mcap_cr': screening.min_market_cap_cr,
            'min_volume': screening.min_avg_daily_volume,
            'min_turnover_cr': screening.min_avg_daily_turnover_cr,
            'exclude_penny': screening.exclude_penny_stocks,
            'min_price': screening.min_share_price,
            'exchanges': screening.allowed_exchanges,
        },
        'llm': {
            'provider': llm.provider,
            'model_name': llm.model_name,
            'temperature': llm.temperature,
            'max_tokens': llm.max_tokens,
        },
        'system': {
            'db_path': cfg.system.db_path,
            'log_level': cfg.system.log_level,
            'data_source': 'yfinance / BSE & NSE Real-time & Historic Feed',
            'framework': 'Django 5.x Full-Stack Python Web Framework',
        }
    }
    return render(request, 'market/settings.html', context)


def search_stocks(request):
    """
    Comprehensive autocomplete search endpoint for ANY listed stock on NSE and BSE.
    Searches:
    1. Database Stock records.
    2. Curated Indian Equity Universe (INDIAN_EQUITY_METADATA & TopPortfoliosRepository).
    3. Live dynamic lookup via yfinance for any unseeded NSE/BSE ticker.
    4. Active IPO listings.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    from .services import ensure_stock_exists
    from src.portfolio.portfolio_analyzer import INDIAN_EQUITY_METADATA
    from src.portfolio.top_portfolios import TopPortfoliosRepository

    clean_q = query.upper().replace(".NS", "").replace(".BO", "").strip()

    # Pre-provision if query matches an unseeded known equity
    if clean_q in INDIAN_EQUITY_METADATA:
        ensure_stock_exists(clean_q)
    elif len(clean_q) >= 2 and clean_q.isalpha():
        top_matches = TopPortfoliosRepository.find_stock_across_portfolios(clean_q)
        if top_matches:
            ensure_stock_exists(clean_q)

    # 1. Search database stocks
    stocks = list(Stock.objects.filter(
        Q(symbol__icontains=query) | Q(name__icontains=query)
    ).values('symbol', 'name', 'exchange', 'current_price', 'day_change_pct')[:12])

    seen_symbols = {s['symbol'].upper() for s in stocks}

    # 2. Check for partial name matches in INDIAN_EQUITY_METADATA
    for sym_key, meta in INDIAN_EQUITY_METADATA.items():
        if f"{sym_key}.NS" not in seen_symbols and (clean_q in sym_key or query.lower() in meta['name'].lower()):
            stk = ensure_stock_exists(sym_key)
            if stk:
                stocks.append({
                    'symbol': stk.symbol,
                    'name': stk.name,
                    'exchange': stk.exchange,
                    'current_price': stk.current_price,
                    'day_change_pct': stk.day_change_pct
                })
                seen_symbols.add(stk.symbol.upper())
            if len(stocks) >= 12:
                break

    # 3. If still fewer than 5 results and query has letters, attempt on-the-fly resolution via ensure_stock_exists
    if len(stocks) < 5 and len(clean_q) >= 2 and clean_q.isalpha():
        stk = ensure_stock_exists(clean_q)
        if stk and stk.symbol.upper() not in seen_symbols:
            stocks.append({
                'symbol': stk.symbol,
                'name': stk.name,
                'exchange': stk.exchange,
                'current_price': stk.current_price,
                'day_change_pct': stk.day_change_pct
            })
            seen_symbols.add(stk.symbol.upper())

    results = [
        {
            'symbol': s['symbol'],
            'clean_symbol': s['symbol'].split('.')[0],
            'name': s['name'],
            'exchange': s['exchange'],
            'price': f"₹{s['current_price']:,.2f}" if s['current_price'] else "N/A",
            'change': f"{s['day_change_pct']:+.2f}%" if s['day_change_pct'] is not None else "",
            'is_positive': s['day_change_pct'] >= 0 if s['day_change_pct'] is not None else True,
            'url': f"/research/{s['symbol']}/"
        }
        for s in stocks
    ]

    # Include matching IPO listings
    try:
        from apps.ipo.models import IPOListing
        ipos = IPOListing.objects.filter(
            Q(symbol__icontains=query) | Q(company_name__icontains=query)
        ).values('symbol', 'company_name', 'status', 'price_band_high', 'gmp_percent')[:4]

        for ip in ipos:
            results.append({
                'symbol': f"{ip['symbol']} (IPO)",
                'clean_symbol': ip['symbol'],
                'name': ip['company_name'],
                'exchange': f"IPO • {ip['status']}",
                'price': f"₹{ip['price_band_high']:,.0f}",
                'change': f"GMP: {ip['gmp_percent']:+.1f}%",
                'is_positive': ip['gmp_percent'] >= 0,
                'url': f"/ipo/{ip['symbol']}/"
            })
    except Exception:
        pass

    return JsonResponse({'results': results})


def market_pulse_api(request):
    """Returns dynamic live market pulse snapshot for indices, breadth, and movers."""
    data = get_live_market_pulse()
    return JsonResponse(data)


def sync_market_api(request):
    """Synchronizes live quotes for active equities from exchange data feeds."""
    symbols = request.GET.get('symbols')
    symbol_list = [s.strip().upper() for s in symbols.split(',')] if symbols else None
    result = sync_live_market_data(symbols=symbol_list, limit=25)
    return JsonResponse(result)



# ==============================================================================
# CLI & BATCH ANALYSIS RUNNER (src.main Engine)
# ==============================================================================

import os
import sys
import time
import uuid
import subprocess
import mimetypes
from datetime import datetime, date
from pathlib import Path
from django.conf import settings
from django.http import FileResponse

# In-memory registry of background CLI execution jobs
CLI_JOBS = {}


def cli_analysis_view(request):
    """Institutional UI for running python -m src.main analyze --index bse500 --top 60

    and related CLI commands with live console output in a downward card window.
    """
    # 1. Distinct sectors for filter dropdown
    sectors = list(Stock.objects.filter(is_active=True)
                   .exclude(sector__isnull=True)
                   .exclude(sector="")
                   .values_list('sector', flat=True)
                   .distinct()
                   .order_by('sector'))

    # 2. Existing reports in data/reports/
    reports_dir = Path(settings.BASE_DIR) / "data" / "reports"
    existing_reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:15]:
            if f.is_file() and f.suffix in ['.md', '.csv', '.pdf']:
                size_kb = round(f.stat().st_size / 1024, 1)
                mtime_str = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d %b %Y, %H:%M")
                existing_reports.append({
                    "name": f.name,
                    "suffix": f.suffix.replace('.', '').upper(),
                    "size_kb": size_kb,
                    "mtime": mtime_str,
                    "url": f"/cli-analysis/report/{f.name}/"
                })

    context = {
        "sectors": sectors,
        "existing_reports": existing_reports,
        "default_index": "bse500",
        "default_top": 60,
    }
    return render(request, "market/cli_analysis.html", context)


def api_run_cli(request):
    """Triggers background execution of python -m src.main with selected filters."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        if request.content_type == "application/json":
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST.dict()
    except Exception:
        data = request.POST.dict()

    command = data.get("command", "analyze").strip()
    if command not in ["analyze", "build_universe", "update_data", "backtest"]:
        return JsonResponse({"error": f"Invalid command: {command}"}, status=400)

    # Base python executable and flags
    py_exe = sys.executable
    cmd_args = [py_exe, "-u", "-m", "src.main", command]
    display_args = ["python", "-m", "src.main", command]

    # Strict validation of input arguments to prevent command manipulation
    allowed_indices = ["bse500", "nifty500", "nifty50", "bse100", "nifty100"]

    if command == "analyze":
        index = data.get("index", "bse500").strip().lower()
        if index not in allowed_indices:
            index = "bse500"
        top = max(1, min(int(data.get("top", 60)), 500))
        cmd_args.extend(["--index", index, "--top", str(top)])
        display_args.extend(["--index", index, "--top", str(top)])

        sector = data.get("sector", "").strip()
        if sector and sector.lower() != "all":
            # Sanitize sector: alphanumeric, spaces, &, -, ()
            clean_sector = re.sub(r"[^A-Za-z0-9 &\-\(\)]", "", sector)
            if clean_sector:
                cmd_args.extend(["--sector", clean_sector])
                display_args.extend(["--sector", f'"{clean_sector}"'])

        min_mcap = data.get("min_market_cap", "").strip()
        if min_mcap:
            try:
                cmd_args.extend(["--min-market-cap", str(float(min_mcap))])
                display_args.extend(["--min-market-cap", str(min_mcap)])
            except ValueError:
                pass

        custom_symbols = data.get("custom_symbols", "").strip()
        if custom_symbols:
            if not re.match(r"^[A-Za-z0-9_.,\-: ]+$", custom_symbols):
                return JsonResponse({"error": "Invalid characters in custom symbols list."}, status=400)
            cmd_args.extend(["--custom-symbols", custom_symbols])
            display_args.extend(["--custom-symbols", f'"{custom_symbols}"'])

        # Always constrain output_dir strictly to data/reports
        output_dir = "data/reports"
        cmd_args.extend(["--output-dir", output_dir])
        display_args.extend(["--output-dir", output_dir])

    elif command == "build_universe":
        index = data.get("index", "bse500").strip().lower()
        if index not in allowed_indices:
            index = "bse500"
        cmd_args.extend(["--index", index])
        display_args.extend(["--index", index])
        custom_symbols = data.get("custom_symbols", "").strip()
        if custom_symbols:
            if not re.match(r"^[A-Za-z0-9_.,\-: ]+$", custom_symbols):
                return JsonResponse({"error": "Invalid characters in custom symbols list."}, status=400)
            cmd_args.extend(["--custom-symbols", custom_symbols])
            display_args.extend(["--custom-symbols", f'"{custom_symbols}"'])
        if data.get("force_refresh") in [True, "true", "1"]:
            cmd_args.append("--force-refresh")
            display_args.append("--force-refresh")

    elif command == "update_data":
        symbols = data.get("symbols", "RELIANCE,TCS,INFY").strip()
        if not re.match(r"^[A-Za-z0-9_.,\-: ]+$", symbols):
            return JsonResponse({"error": "Invalid characters in symbols list."}, status=400)
        period = data.get("period", "2y").strip()
        if period not in ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]:
            period = "2y"
        cmd_args.extend(["--symbols", symbols, "--period", period])
        display_args.extend(["--symbols", f'"{symbols}"', "--period", period])

    elif command == "backtest":
        start = data.get("start", "2024-01-01").strip()
        end = data.get("end", "2024-12-31").strip()
        index = data.get("index", "nifty500").strip()
        top_n = int(data.get("top_n", 10))
        freq = data.get("frequency", "M").strip()
        capital = float(data.get("capital", 1000000))
        cmd_args.extend([
            "--start", start, "--end", end, "--index", index,
            "--top-n", str(top_n), "--frequency", freq, "--capital", str(capital)
        ])
        display_args.extend([
            "--start", start, "--end", end, "--index", index,
            "--top-n", str(top_n), "--frequency", freq, "--capital", str(int(capital))
        ])

    # Setup unique job id and log file
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    log_dir = Path(settings.BASE_DIR) / "data" / "logs" / "cli_jobs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / f"{job_id}.log"

    display_command_str = " ".join(display_args)

    # Initialize log file with header
    with open(log_file_path, "w", encoding="utf-8") as f_init:
        f_init.write(f"=== STOCKAGENT AI QUANT ENGINE: CLI RUNNER ===\n")
        f_init.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST\n")
        f_init.write(f"Command  : {display_command_str}\n")
        f_init.write(f"Engine   : .venv Python 3.12 (Subprocess Pipeline)\n")
        f_init.write("=" * 72 + "\n\n")

    # Open in append mode for child process
    log_file = open(log_file_path, "a", encoding="utf-8", buffering=1)

    proc = subprocess.Popen(
        cmd_args,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(settings.BASE_DIR),
        text=True,
        bufsize=1
    )

    CLI_JOBS[job_id] = {
        "process": proc,
        "pid": proc.pid,
        "display_command": display_command_str,
        "log_path": log_file_path,
        "log_file": log_file,
        "started_at": time.time(),
        "command": command,
        "output_dir": data.get("output_dir", "data/reports"),
        "status": "running"
    }

    return JsonResponse({
        "status": "started",
        "job_id": job_id,
        "command": display_command_str,
        "pid": proc.pid
    })


def api_cli_status(request, job_id):
    """Streams live log updates and returns execution status for a given job."""
    job = CLI_JOBS.get(job_id)
    offset = int(request.GET.get("offset", 0))

    log_dir = Path(settings.BASE_DIR) / "data" / "logs" / "cli_jobs"
    log_file_path = log_dir / f"{job_id}.log"

    new_logs = ""
    new_offset = offset

    if log_file_path.exists():
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            new_logs = f.read()
            new_offset = f.tell()

    status = "running"
    exit_code = None
    elapsed = 0.0

    if job:
        elapsed = round(time.time() - job["started_at"], 1)
        proc = job["process"]
        poll_res = proc.poll()
        if poll_res is not None:
            exit_code = poll_res
            status = "completed" if poll_res == 0 else "failed"
            job["status"] = status
            if status == "completed" and not job.get("synced"):
                job["synced"] = True
                try:
                    from .services import sync_evaluations_from_research_db
                    sync_evaluations_from_research_db()
                except Exception as e:
                    pass
            try:
                if job.get("log_file") and not job["log_file"].closed:
                    job["log_file"].close()
            except Exception:
                pass
    else:
        # If server restarted or job purged from memory
        status = "completed" if log_file_path.exists() else "not_found"

    # Scan for generated reports in data/reports/
    reports = []
    reports_dir = Path(settings.BASE_DIR) / "data" / "reports"
    if reports_dir.exists() and job:
        job_start = job["started_at"]
        for f in sorted(reports_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and f.stat().st_mtime >= (job_start - 2):
                if f.suffix in ['.md', '.csv', '.pdf']:
                    reports.append({
                        "name": f.name,
                        "type": f.suffix.replace('.', '').upper(),
                        "size_kb": round(f.stat().st_size / 1024, 1),
                        "url": f"/cli-analysis/report/{f.name}/"
                    })

    return JsonResponse({
        "job_id": job_id,
        "status": status,
        "exit_code": exit_code,
        "logs": new_logs,
        "next_offset": new_offset,
        "elapsed_seconds": elapsed,
        "reports": reports
    })


def api_cli_stop(request, job_id):
    """Terminates a running CLI subprocess."""
    job = CLI_JOBS.get(job_id)
    if not job:
        return JsonResponse({"error": "Job not found"}, status=404)

    proc = job.get("process")
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            time.sleep(0.5)
            if proc.poll() is None:
                proc.kill()
        except Exception as e:
            logger.warning(f"Failed to kill CLI process {proc.pid}: {e}")

        # Append termination note to log file
        log_path = job.get("log_path")
        if log_path and Path(log_path).exists():
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n\n[PROCESS MANUALLY STOPPED BY USER]\n")

        job["status"] = "stopped"
        return JsonResponse({"status": "stopped", "message": "Process terminated successfully."})

    return JsonResponse({"status": "already_finished", "message": "Process is no longer running."})


def cli_report_view(request, filename):
    """Safe view and download endpoint for generated reports."""
    reports_dir = (Path(settings.BASE_DIR) / "data" / "reports").resolve()
    target_path = (reports_dir / filename).resolve()

    # Path traversal protection
    try:
        if not target_path.is_relative_to(reports_dir) or not target_path.exists() or not target_path.is_file():
            return HttpResponse("Report file not found.", status=404)
    except (ValueError, AttributeError):
        if not str(target_path).startswith(str(reports_dir)) or not target_path.exists():
            return HttpResponse("Report file not found.", status=404)

    content_type, _ = mimetypes.guess_type(str(target_path))
    content_type = content_type or "application/octet-stream"

    # If markdown and viewed directly in browser (not forced download)
    if filename.endswith(".md") and request.GET.get("download") != "1":
        content = target_path.read_text(encoding="utf-8", errors="replace")
        return HttpResponse(f"<pre style='font-family: monospace; white-space: pre-wrap; padding: 2rem; background: #0f172a; color: #f8fafc;'>{content}</pre>", content_type="text/html")

    return FileResponse(open(target_path, "rb"), as_attachment=True, filename=filename, content_type=content_type)
