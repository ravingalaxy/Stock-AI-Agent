from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404

from apps.market.models import Stock, PriceHistory, AgentEvaluation, BacktestRunRecord
from apps.market.services import get_market_indices_summary, seed_universe_if_empty
from .serializers import (
    StockSerializer, PriceHistorySerializer,
    AgentEvaluationSerializer, BacktestRunRecordSerializer
)


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint to list and retrieve stocks with search and filters."""
    queryset = Stock.objects.filter(is_active=True).order_by('symbol')
    serializer_class = StockSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['symbol', 'name', 'sector', 'industry']
    ordering_fields = ['market_cap', 'current_price', 'day_change_pct', 'pe_ratio']


class StockPriceHistoryAPIView(generics.ListAPIView):
    """Retrieve historical daily OHLCV prices for a specific stock."""
    serializer_class = PriceHistorySerializer

    def get_queryset(self):
        symbol = self.kwargs['symbol']
        return PriceHistory.objects.filter(stock__symbol__iexact=symbol).order_by('-date')[:365]


class RankingsListAPIView(generics.ListAPIView):
    """Retrieve ranked watchlist for latest evaluation run."""
    serializer_class = AgentEvaluationSerializer

    def get_queryset(self):
        seed_universe_if_empty()
        latest_date = AgentEvaluation.objects.filter(rank__gt=0).order_by('-evaluation_date').values_list('evaluation_date', flat=True).first()
        qs = AgentEvaluation.objects.filter(rank__gt=0).select_related('stock')
        if latest_date:
            qs = qs.filter(evaluation_date=latest_date)
        return qs.order_by('rank')


class MarketSummaryAPIView(APIView):
    """Returns live indices and market overview metrics."""
    def get(self, request, *args, **kwargs):
        seed_universe_if_empty()
        indices = get_market_indices_summary()
        stocks = Stock.objects.filter(is_active=True)
        advances = stocks.filter(day_change__gt=0).count()
        declines = stocks.filter(day_change__lt=0).count()
        return Response({
            'indices': indices,
            'breadth': {
                'total': stocks.count(),
                'advances': advances,
                'declines': declines,
                'unchanged': stocks.count() - (advances + declines)
            }
        })


class IPOListAPIView(APIView):
    """Returns active upcoming and ongoing IPO offerings strictly."""
    def get(self, request, *args, **kwargs):
        from apps.ipo.models import IPOListing
        from apps.ipo.services import seed_ipo_universe_if_empty
        seed_ipo_universe_if_empty()

        ACTIVE_STATUSES = ['Upcoming', 'Open', 'Ongoing', 'ongoing']
        ipos = IPOListing.objects.filter(status__in=ACTIVE_STATUSES).order_by('-composite_score')
        data = [
            {
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
            }
            for ip in ipos
        ]
        return Response({'count': len(data), 'results': data})
