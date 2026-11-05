"""Global template context processor for market status and stats."""

from datetime import datetime, time
import pytz
from django.conf import settings
from .models import Stock, AgentEvaluation
from .services import get_market_indices_summary


def market_context(request):
    """Provides market hours status, live indices, counts, and disclaimer to all templates."""
    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = now_ist.time()
    weekday = now_ist.weekday()  # 0 is Monday, 4 is Friday, 5 is Saturday, 6 is Sunday

    # NSE/BSE regular market hours: 09:15 AM to 03:30 PM, Monday to Friday
    market_open_time = time(9, 15)
    market_close_time = time(15, 30)

    is_open = (weekday < 5) and (market_open_time <= current_time <= market_close_time)

    # Market metrics
    universe_count = Stock.objects.filter(is_active=True).count()
    ranked_count = AgentEvaluation.objects.filter(evaluation_date=now_ist.date()).count()

    # Dynamic indices summary
    indices = get_market_indices_summary(force_refresh=False)

    return {
        'MARKET_IS_OPEN': is_open,
        'MARKET_TIME_IST': now_ist.strftime('%d %b %Y, %I:%M %p IST'),
        'UNIVERSE_TOTAL_COUNT': universe_count,
        'RANKED_TODAY_COUNT': ranked_count,
        'LIVE_INDICES': indices,
        'COMPLIANCE_DISCLAIMER': getattr(settings, 'DISCLAIMER', ''),
    }
