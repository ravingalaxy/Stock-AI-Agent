"""Portfolio Management & Risk Monitoring Engine.

Implements Section 4 Portfolio Tools:
- Watchlist creation
- Current holdings & profit/loss tracking (INR & %)
- Position-size calculator (Conservative 5-10%, Aggressive, Half-Kelly, Capital-at-risk)
- Stop-loss & target-price calculator (ATR-based, percentage-based, risk/reward ratio)
- Sector-allocation analysis
- Concentration alerts:
  * Maximum 5–10% position size per stock for conservative users
  * Alert: No single stock above 20% of the portfolio
  * Alert: No sector above 30% of the portfolio
- Simple rebalancing suggestions
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from src.utils.logger import logger
from src.utils.helpers import safe_divide, format_inr, format_percentage


@dataclass
class HoldingItem:
    """Represents a portfolio holding."""
    symbol: str
    company_name: str
    sector: str
    quantity: int
    buy_price: float
    current_price: float

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
        return safe_divide(self.pnl_amount, self.invested_value) * 100.0


def get_sample_holdings() -> List[HoldingItem]:
    """Provides a realistic sample portfolio for Indian equity investors."""
    return [
        HoldingItem("RELIANCE.NS", "Reliance Industries Limited", "Energy & Petrochemicals", 50, 2810.0, 2940.50),
        HoldingItem("TCS.NS", "Tata Consultancy Services", "Information Technology", 35, 3650.0, 3890.00),
        HoldingItem("HDFCBANK.NS", "HDFC Bank Limited", "Financial Services", 80, 1540.0, 1680.25),
        HoldingItem("INFY.NS", "Infosys Limited", "Information Technology", 60, 1420.0, 1510.40),
        HoldingItem("ITC.NS", "ITC Limited", "Consumer Goods", 200, 430.0, 488.50),
        HoldingItem("BHARTIARTL.NS", "Bharti Airtel Limited", "Telecommunication", 75, 1320.0, 1540.00),
        HoldingItem("LT.NS", "Larsen & Toubro Limited", "Capital Goods & Infra", 25, 3350.0, 3520.00),
    ]


class PortfolioManager:
    """Manages holdings, risk limits, position sizing, and rebalancing suggestions."""

    def __init__(self, max_single_stock_pct: float = 20.0, max_sector_pct: float = 30.0):
        self.max_single_stock_pct = max_single_stock_pct  # Hard cap: 20%
        self.max_sector_pct = max_sector_pct              # Hard cap: 30%
        self.conservative_stock_pct = 10.0                # Conservative user limit: 5-10%

    def evaluate_portfolio(self, holdings: List[HoldingItem]) -> Dict[str, Any]:
        """Compute portfolio metrics, P&L, sector allocations, concentration alerts, and rebalance suggestions."""
        if not holdings:
            return {
                'total_invested': 0.0,
                'total_current': 0.0,
                'total_pnl': 0.0,
                'total_pnl_pct': 0.0,
                'holdings_count': 0,
                'holdings_summary': [],
                'sector_allocation': {},
                'alerts': [],
                'rebalancing_suggestions': []
            }

        total_invested = sum(h.invested_value for h in holdings)
        total_current = sum(h.current_value for h in holdings)
        total_pnl = total_current - total_invested
        total_pnl_pct = safe_divide(total_pnl, total_invested) * 100.0

        # Detailed holding items with weights
        holdings_summary = []
        sector_values: Dict[str, float] = {}

        for h in holdings:
            weight = safe_divide(h.current_value, total_current) * 100.0 if total_current > 0 else 0.0
            holdings_summary.append({
                'symbol': h.symbol,
                'company_name': h.company_name,
                'sector': h.sector,
                'quantity': h.quantity,
                'buy_price': h.buy_price,
                'current_price': h.current_price,
                'invested_value': round(h.invested_value, 2),
                'current_value': round(h.current_value, 2),
                'weight_pct': round(weight, 2),
                'pnl_amount': round(h.pnl_amount, 2),
                'pnl_pct': round(h.pnl_pct, 2),
                'is_profit': h.pnl_amount >= 0
            })
            sec = h.sector or "Unclassified"
            sector_values[sec] = sector_values.get(sec, 0.0) + h.current_value

        # Sector Allocations
        sector_allocation = {}
        for sec, val in sector_values.items():
            sec_weight = safe_divide(val, total_current) * 100.0 if total_current > 0 else 0.0
            sector_allocation[sec] = {
                'value': round(val, 2),
                'weight_pct': round(sec_weight, 2)
            }

        # Concentration Alerts & Risk Rules
        alerts = []
        rebalancing_suggestions = []

        # 1. Single stock concentration check
        for h_sum in holdings_summary:
            w = h_sum['weight_pct']
            sym = h_sum['symbol']
            if w > self.max_single_stock_pct:
                alerts.append({
                    'category': 'single_stock',
                    'severity': 'danger',
                    'level': 'CRITICAL',
                    'title': f'Single Stock Concentration Breach: {sym}',
                    'message': f'{sym} constitutes {w:.1f}% of total portfolio value, exceeding the strict 20% risk limit.'
                })
                # Rebalance suggestion: trim to 15%
                excess_val = (w - 15.0) / 100.0 * total_current
                shares_to_trim = int(excess_val / h_sum['current_price']) if h_sum['current_price'] > 0 else 0
                if shares_to_trim > 0:
                    rebalancing_suggestions.append({
                        'symbol': sym,
                        'action': 'TRIM',
                        'shares': shares_to_trim,
                        'reason': f'Trim position weight from {w:.1f}% down to 15.0% to enforce single-stock diversification.'
                    })
            elif w > self.conservative_stock_pct:
                alerts.append({
                    'category': 'single_stock',
                    'severity': 'warning',
                    'level': 'WARNING',
                    'title': f'Conservative Allocation Notice: {sym}',
                    'message': f'{sym} is {w:.1f}% of portfolio. For conservative risk profiles, limit position sizes to 5-10%.'
                })

        # 2. Sector concentration check
        for sec, sec_data in sector_allocation.items():
            w_sec = sec_data['weight_pct']
            if w_sec > self.max_sector_pct:
                alerts.append({
                    'category': 'sector',
                    'severity': 'danger',
                    'level': 'CRITICAL',
                    'title': f'Sector Over-Concentration: {sec}',
                    'message': f'{sec} sector allocation is {w_sec:.1f}%, exceeding the maximum 30% sector concentration limit.'
                })
                rebalancing_suggestions.append({
                    'symbol': f"Sector: {sec}",
                    'action': 'DIVERSIFY',
                    'shares': 0,
                    'reason': f'Total {sec} exposure is {w_sec:.1f}%. Avoid adding further exposure to this sector and reallocate fresh capital into under-represented sectors.'
                })

        return {
            'total_invested': round(total_invested, 2),
            'total_current': round(total_current, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
            'holdings_count': len(holdings),
            'holdings_summary': sorted(holdings_summary, key=lambda x: x['current_value'], reverse=True),
            'sector_allocation': sector_allocation,
            'alerts': alerts,
            'rebalancing_suggestions': rebalancing_suggestions
        }

    @classmethod
    def calculate_position_size(
        cls,
        portfolio_capital: float,
        risk_profile: str = "conservative",
        entry_price: float = 1000.0,
        stop_loss_price: Optional[float] = None,
        risk_per_trade_pct: float = 1.5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calculate recommended position sizing based on risk rules.
        Conservative users: 5-10% position size.
        Aggressive / Capital-at-risk: Based on maximum allowed loss per trade.
        """
        if portfolio_capital <= 0 or entry_price <= 0:
            return {'error': 'Invalid capital or entry price'}

        risk_pct = kwargs.get('risk_pct', risk_per_trade_pct)
        risk_amount = portfolio_capital * (risk_pct / 100.0)

        # Loss per share
        if stop_loss_price and stop_loss_price < entry_price:
            loss_per_share = entry_price - stop_loss_price
        else:
            loss_per_share = entry_price * 0.05

        risk_sized_shares = int(risk_amount / loss_per_share) if loss_per_share > 0 else 0

        # Hard cap: 20%
        hard_cap_val = portfolio_capital * 0.20
        hard_cap_shares = int(hard_cap_val / entry_price)

        # Conservative: 10%
        cons_max_val = portfolio_capital * 0.10
        cons_max_shares = max(int(cons_max_val / entry_price), 1)

        if 'risk_pct' in kwargs and stop_loss_price:
            rec_shares = min(risk_sized_shares, hard_cap_shares) if risk_sized_shares > 0 else cons_max_shares
        elif risk_profile.lower() == "conservative":
            rec_shares = min(cons_max_shares, hard_cap_shares)
        elif risk_profile.lower() == "aggressive" and risk_sized_shares:
            rec_shares = min(risk_sized_shares, hard_cap_shares)
        else:
            rec_shares = cons_max_shares

        pos_val = rec_shares * entry_price
        pos_pct = safe_divide(pos_val, portfolio_capital) * 100.0

        return {
            'recommended_shares': rec_shares,
            'recommended_investment': round(pos_val, 2),
            'position_capital': round(pos_val, 2),
            'position_weight_pct': round(pos_pct, 1),
            'max_loss_inr': round(rec_shares * loss_per_share, 2),
            'risk_per_share': round(loss_per_share, 2),
            'is_conservative_compliant': pos_pct <= 10.0,
            'conservative_max_shares': cons_max_shares,
            'conservative_max_inr': round(cons_max_val, 2),
            'hard_cap_max_shares': hard_cap_shares,
            'hard_cap_max_inr': round(hard_cap_val, 2),
            'risk_per_trade_amount': round(risk_amount, 2),
            'disclaimer': 'Use position sizing and stop-losses as risk-management tools only, not guaranteed protection.'
        }

    @classmethod
    def calculate_stop_target(
        cls,
        entry_price: float,
        risk_pct: float = 5.0,
        target_ratio: float = 2.0,
        atr_val: Optional[float] = None,
        atr_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """Calculates stop-loss and multiple target prices based on risk percentage or ATR."""
        if atr_val and atr_val > 0:
            sl_distance = atr_val * atr_multiplier
        else:
            sl_distance = entry_price * (risk_pct / 100.0)

        sl_price = entry_price - sl_distance
        downside_pct = (sl_distance / entry_price) * 100.0
        t1_price = entry_price + (sl_distance * 1.5)
        t2_price = entry_price + (sl_distance * target_ratio)

        return {
            'stop_loss_price': round(max(sl_price, 0.0), 2),
            'downside_risk_pct': round(downside_pct, 2),
            'target_price_1': round(t1_price, 2),
            'target_1_gain_pct': round((t1_price - entry_price) / entry_price * 100.0, 2),
            'target_price_2': round(t2_price, 2),
            'target_2_gain_pct': round((t2_price - entry_price) / entry_price * 100.0, 2),
        }
    @staticmethod
    def calculate_stop_loss_and_target(
        entry_price: float,
        atr_14: Optional[float] = None,
        risk_reward_ratio: float = 2.0,
        stop_loss_pct: float = 6.0
    ) -> Dict[str, Any]:
        """
        Calculate stop-loss and target prices based on ATR volatility and risk-reward ratio.
        """
        if entry_price <= 0:
            return {'error': 'Invalid entry price'}

        # If ATR is available, use 1.8x ATR trailing stop
        if atr_14 and atr_14 > 0:
            sl_distance = atr_14 * 1.8
            sl_price = entry_price - sl_distance
            actual_sl_pct = (sl_distance / entry_price) * 100.0
            method = "1.8x ATR Volatility"
        else:
            actual_sl_pct = stop_loss_pct
            sl_distance = entry_price * (stop_loss_pct / 100.0)
            sl_price = entry_price - sl_distance
            method = f"{stop_loss_pct}% Fixed Risk"

        target_distance = sl_distance * risk_reward_ratio
        target_price = entry_price + target_distance
        target_gain_pct = (target_distance / entry_price) * 100.0

        return {
            'entry_price': round(entry_price, 2),
            'stop_loss_price': round(max(sl_price, 0.0), 2),
            'stop_loss_pct': round(actual_sl_pct, 1),
            'target_price': round(target_price, 2),
            'target_gain_pct': round(target_gain_pct, 1),
            'risk_reward_ratio': f"1 : {risk_reward_ratio:.1f}",
            'calculation_method': method,
            'risk_disclaimer': 'Stop-losses are automated risk controls and do not guarantee execution prices in fast or gapping markets.'
        }
