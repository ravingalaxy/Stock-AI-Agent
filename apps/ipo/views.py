"""
Views for IPO Intelligence, 9 Legendary Strategy Evaluation, and Prospectus Forensics.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from apps.ipo.models import IPOListing
from apps.ipo.services import (
    seed_ipo_universe_if_empty,
    sync_ipo_universe,
    update_all_ipo_statuses
)


def ipo_dashboard(request):
    """Institutional IPO Surveillance Center covering active, open, upcoming, and listed NSE/BSE offerings."""
    seed_ipo_universe_if_empty()
    # Always ensure statuses are kept in sync with the current date
    update_all_ipo_statuses()

    view_filter = request.GET.get('view', '').strip().lower()
    status_filter = request.GET.get('status', 'all').strip().lower()
    category_filter = request.GET.get('category', 'all').strip()
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', '-composite_score').strip()

    # Dynamic status filtering
    if view_filter == 'listed':
        ipos = IPOListing.objects.filter(status__iexact='Listed')
    elif status_filter in ['open', 'ongoing']:
        ipos = IPOListing.objects.filter(status__in=['Open', 'Ongoing', 'ongoing'])
    elif status_filter == 'upcoming':
        ipos = IPOListing.objects.filter(status__iexact='Upcoming')
    elif status_filter == 'closed':
        ipos = IPOListing.objects.filter(status__iexact='Closed')
    elif status_filter == 'everything':
        ipos = IPOListing.objects.all()
    elif status_filter == 'listed':
        ipos = IPOListing.objects.none()
    else:
        # Default 'all' pipeline view: includes active pipeline issues (Upcoming, Open, Ongoing, and recently Closed awaiting listing)
        ipos = IPOListing.objects.filter(status__in=['Upcoming', 'Open', 'Ongoing', 'ongoing', 'Closed'])

    if category_filter and category_filter.lower() != 'all':
        ipos = ipos.filter(category__iexact=category_filter)

    if search_query:
        if search_query.lower() in ['ongoing', 'open']:
            ipos = ipos.filter(status__in=['Open', 'Ongoing', 'ongoing'])
        elif search_query.lower() == 'upcoming':
            ipos = ipos.filter(status__iexact='Upcoming')
        elif search_query.lower() == 'listed':
            ipos = ipos.filter(status__iexact='Listed')
        elif search_query.lower() == 'closed':
            ipos = ipos.filter(status__iexact='Closed')
        else:
            ipos = ipos.filter(
                Q(company_name__icontains=search_query) |
                Q(symbol__icontains=search_query) |
                Q(sector__icontains=search_query)
            )

    valid_sorts = {
        'score_desc': '-composite_score',
        'score_asc': 'composite_score',
        'gmp_desc': '-gmp_percent',
        'size_desc': '-issue_size_cr',
        'date_desc': '-open_date',
        'listing_desc': '-listing_date'
    }
    order_clause = valid_sorts.get(sort_by, '-composite_score')
    ipos = ipos.order_by(order_clause)

    # Summary Statistics
    all_qs = IPOListing.objects.all()
    total_active_count = all_qs.filter(status__in=['Upcoming', 'Open', 'Ongoing', 'ongoing', 'Closed']).count()
    open_count = all_qs.filter(status__in=['Open', 'Ongoing', 'ongoing']).count()
    upcoming_count = all_qs.filter(status__iexact='Upcoming').count()
    closed_count = all_qs.filter(status__iexact='Closed').count()
    listed_count = all_qs.filter(status__iexact='Listed').count()
    all_count = all_qs.count()

    active_gmps = [ip.gmp_percent for ip in all_qs.filter(status__in=['Upcoming', 'Open', 'Ongoing', 'ongoing']) if ip.gmp_percent is not None]
    avg_gmp = (sum(active_gmps) / len(active_gmps)) if active_gmps else 0.0

    context = {
        'ipos': ipos,
        'status_filter': status_filter,
        'view_filter': view_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'search_query': search_query,
        'total_count': total_active_count,
        'open_count': open_count,
        'upcoming_count': upcoming_count,
        'closed_count': closed_count,
        'listed_count': listed_count,
        'all_count': all_count,
        'avg_gmp': round(avg_gmp, 1),
    }
    return render(request, 'ipo/ipo_dashboard.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_sync_ipo_data(request):
    """Refreshes and synchronizes IPO statuses with real-time exchange listing status."""
    try:
        updated = update_all_ipo_statuses()
        all_qs = IPOListing.objects.all()
        total_active = all_qs.filter(status__in=['Upcoming', 'Open', 'Ongoing', 'ongoing', 'Closed']).count()
        open_count = all_qs.filter(status__in=['Open', 'Ongoing', 'ongoing']).count()
        upcoming_count = all_qs.filter(status__iexact='Upcoming').count()
        closed_count = all_qs.filter(status__iexact='Closed').count()
        listed_count = all_qs.filter(status__iexact='Listed').count()

        return JsonResponse({
            'status': 'success',
            'message': f'IPO pipeline synchronized successfully. {updated} listing statuses updated based on live dates.',
            'updated': updated,
            'total_active': total_active,
            'open_count': open_count,
            'upcoming_count': upcoming_count,
            'closed_count': closed_count,
            'listed_count': listed_count,
            'all_count': all_qs.count()
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def ipo_detail(request, symbol: str):
    """Deep-Dive Institutional Prospectus Forensics & 9 Legendary Strategy Breakdown."""
    seed_ipo_universe_if_empty()
    update_all_ipo_statuses()

    ipo = get_object_or_404(IPOListing, symbol__iexact=symbol)

    # Peers in the same sector
    peers = IPOListing.objects.filter(sector=ipo.sector).exclude(symbol=ipo.symbol)[:4]

    context = {
        'ipo': ipo,
        'strategies': ipo.strategies,
        'thesis_invalidations': ipo.thesis_invalidations,
        'peers': peers,
    }
    return render(request, 'ipo/ipo_detail.html', context)


def api_ipo_list(request):
    """JSON API endpoint listing active and upcoming IPOs strictly."""
    seed_ipo_universe_if_empty()
    update_all_ipo_statuses()
    ACTIVE_STATUSES = ['Upcoming', 'Open', 'Ongoing', 'ongoing']
    ipos = IPOListing.objects.filter(status__in=ACTIVE_STATUSES).order_by('-composite_score')
    data = []
    for ip in ipos:
        data.append({
            'symbol': ip.symbol,
            'company_name': ip.company_name,
            'sector': ip.sector,
            'status': ip.status,
            'price_band': f"₹{ip.price_band_low:.0f} - ₹{ip.price_band_high:.0f}",
            'issue_size_cr': ip.issue_size_cr,
            'fresh_ratio_pct': ip.fresh_ratio_pct,
            'ofs_ratio_pct': ip.ofs_ratio_pct,
            'gmp_percent': ip.gmp_percent,
            'composite_score': ip.composite_score,
            'recommendation': ip.recommendation
        })
    return JsonResponse({'status': 'success', 'count': len(data), 'ipos': data})


def api_ipo_detail(request, symbol: str):
    """JSON API endpoint returning detailed forensic IPO evaluation."""
    seed_ipo_universe_if_empty()
    update_all_ipo_statuses()
    ipo = get_object_or_404(IPOListing, symbol__iexact=symbol)
    return JsonResponse({
        'status': 'success',
        'symbol': ipo.symbol,
        'company_name': ipo.company_name,
        'status_val': ipo.status,
        'composite_score': ipo.composite_score,
        'recommendation': ipo.recommendation,
        'financials': {
            'revenue_3y_cagr': ipo.revenue_3y_cagr,
            'pat_3y_cagr': ipo.pat_3y_cagr,
            'pre_roe': ipo.pre_roe,
            'pre_roce': ipo.pre_roce,
            'debt_to_equity': ipo.debt_to_equity,
            'post_pe': ipo.post_pe,
            'industry_pe': ipo.industry_pe
        },
        'strategies': ipo.strategies,
        'thesis_invalidations': ipo.thesis_invalidations
    })
