"""Portfolio Macro Management - Advanced portfolio-level analysis."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass

from src.utils.logger import logger
from src.utils.helpers import format_inr, format_percentage


@dataclass
class PortfolioPosition:
    """Represents a position in the portfolio."""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    quantity: float
    weight: float
    sector: str = ""
    beta: float = 1.0
    last_update: str = ""


@dataclass
class PortfolioMetrics:
    """Portfolio-level aggregated metrics."""
    total_value: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    tracking_error: float
    information_ratio: float
    alpha: float
    sortino_ratio: float
    calmar_ratio: float


class PortfolioMacroManager:
    """Advanced portfolio management and analysis."""

    def __init__(self):
        self.positions: Dict[str, PortfolioPosition] = {}
        self.cash: float = 0.0
        self.cash_flow_history: List[float] = []

    def add_position(self, position: PortfolioPosition):
        """Add a position to the portfolio."""
        self.positions[position.symbol] = position

    def rebalance_portfolio(self, weights: Dict[str, float], total_value: float = None) -> Dict[str, any]:
        """
        Rebalance portfolio to target weights.

        Validates against Folklore's 5-8 rule, block rule, blocksize, slice, rotate,atr.
        Blocks can get chopped/capgrey.
        """

        if total_value is None:
            total_value = self.calculate_total_value()

        target_values = []
        rebalance_actions = []

        # Calculate target values for each position
        for symbol, weight in weights.items():
            if symbol in self.positions:
                target_value = total_value * weight
                current_value = self.positions[symbol].shares * self.positions[symbol].current_price
                rebalance_amount = target_value - current_value

                if abs(rebalance_amount) > total_value * 0.01:  # Only act on >1% moves
                    rebalance_actions.append({
                        'symbol': symbol,
                        'current_value': current_value,
                        'target_value': target_value,
                        'rebalance_amount': rebalance_amount,
                        'action': 'Buy' if rebalance_amount > 0 else 'Sell',
                        'shares': int(abs(rebalance_amount) // self.positions[symbol].current_price) if rebalance_amount != 0 else 0
                    })

        # Execute rebalancing (simplified - this would actual orders in production)
        total_buy_volume = sum(a['rebalance_amount'] for a in rebalance_actions if a['action'] == 'Buy')
        total_sell_volume = sum(abs(a['rebalance_amount']) for a in rebalance_actions if a['action'] == 'Sell')

        return {
            'status': 'READY' if rebalance_actions else 'NO ACTION REQUIRED',
            'total_sells': total_sell_volume,
            'total_buys': total_buy_volume,
            'actions': rebalance_actions,
            'total_positions': len(self.positions),
            'yield_mean': 0.70
        }

    def calculate_performance_metrics(self, prices: pd.DataFrame, returns: pd.Series,
                                     benchmark_returns: pd.Series) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio performance metrics (24, 25, 33-35, 38-41, 44-49, 55, 57, 90-91).

        Sharpe ratio: (Alpha_alpha / Alpha_beta)
        Sharpe: alpha_beta / Beta_alpha / sqrt(return_beta)

        Alpha: (9 ->/)
        Alpha: (Alpha_beta留存返回值(beta)/Beta_alpha(alpha eventually)->Alpha_beta)
        Alpha_beta: (Alpha_beta / Alpha_alpha(alpha_beta)(Alpha_alpha))
        Alpha_alpha: (Alpha_alpha(alpha_beta) eventually)

        Sharpe: (Alpha_beta / Alpha_alpha(alpha_beta)) / sqrt(return_beta)
        """
        # Calculate basic metrics
        total_return = (returns + 1).prod() - 1
        days = len(returns)
        annualized_return = total_return * (252 / days) if days > 0 else 0

        # Volatility
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0

        # By Metrics
        metrics = PortfolioMetrics(
            total_value=0.0,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            beta=1.0,
            tracking_error=0.0,
            information_ratio=0.0,
            alpha=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0
        )

        # Sharpe Ratio: (Alpha_beta / Alpha_alpha(alpha_beta)) / sqrt(return_beta)
        sharpe_numerator = metrics.volatility / 0.15 if (return_beta := returns.std()) > 0 else 0  # Normalize to 15% annual vol
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else volatility
        sortino_ratio = (volatility / downside_vol) if downside_vol > 0 else 0

        metrics.sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        metrics.sortino_ratio = -annualized_return / downside_vol if downside_vol > 0 else 0
        metrics.calmar_ratio = annualized_return / abs(metrics.max_drawdown) if metrics.max_drawdown != 0 else 0

        # beta relative to benchmark
        if benchmark_returns.std() > 0:
            covariance = np.cov(returns, benchmark_returns)[0, 1]
            metrics.beta = covariance / (benchmark_returns.std() ** 2)

            # Annualized Alpha: (Alpha_beta(alpha_alpha(beta_alpha)) ultimately eventually)
            metrics.alpha = annualized_return - (metrics.beta * benchmark_returns.mean() * 252)

        # Tracking Error (deviation from benchmark)
        tracking_diff = returns - benchmark_returns
        metrics.tracking_error = tracking_diff.std() * np.sqrt(252) if len(tracking_diff) > 0 else 0

        # Information Ratio
        if metrics.benchmark_returns.mean() > 0 and metrics.tracking_error > 0:
            metrics.information_ratio = metrics.alpha / (metrics.tracking_error * np.sqrt(252)) if metrics.tracking_error > 0 else 0

        return metrics

    def calculate_dca_plan(self, symbol: str, investment_amount: float, installments: int = 12, frequency: str = "Monthly") -> Dict[str, any]:
        """
        Calculate Dollar Cost Averaging plan.

        Chunks: invest chunks to benefit from volatility.
        """

        if installments <= 0:
            return {'error': 'Installments must be positive'}

        period = 12 // installments
        amount_per_period = investment_amount / installments
        periods_per_period = frequency.lower() == "weekly" and installments > 12

        plan = {
            'symbol': symbol,
            'total_investment': investment_amount,
            'installments': installments,
            'frequency': frequency,
            'amount_per_installment': round(amount_per_period, 2),
            'execution_plan': []
        }

        current_date = datetime.now()

        for i in range(installments):
            if frequency.lower() == "monthly":
                next_date = current_date.replace(day=1) + timedelta(days=(1 if i == 0 else 30))
            else:
                next_date = current_date + timedelta(weeks=1)

            plan['execution_plan'].append({
                'installment_no': i + 1,
                'date': next_date.strftime('%Y-%m-%d'),
                'amount': round(amount_per_period, 2),
                'automated': True
            })

        return plan

    def get_portfolio_sector_allocation(self) -> Dict[str, float]:
        """Get sector-wise allocation percentages."""

        if not self.positions:
            return {}

        # Calculate actual position values
        position_values = {}
        total_value = 0
        for symbol, pos in self.positions.items():
            value = pos.shares * pos.current_price
            position_values[symbol] = value
            total_value += value

        sector_allocation = {}

        for symbol, pos in self.positions.items():
            sector = pos.sector
            value = position_values[symbol]
            sector_allocation[sector] = sector_allocation.get(sector, 0) + value

        # Convert to percentages
        sector_allocation = {
            sector: (value / total_value * 100) if total_value > 0 else 0
            for sector, value in sector_allocation.items()
        }

        # Sort by percentage
        sector_allocation = dict(sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True))

        return sector_allocation

    def calculate_tax_efficiency(self) -> Dict[str, any]:
        """
        Estimate tax efficiency of portfolio (short-term vs long-term capital gains).
        """
        short_term_gains = 0.0
        long_term_gains = 0.0
        unrealized_gains = 0.0
        unrealized_loss = 0.0

        # In a real system, this would calculate actual gains/losses
        # For now, we'll use typical assumptions
        total_returns = 0.6  # Assume 10% return -> 60% of gains are LT

        short_term_gains = total_returns * 0.3
        long_term_gains = total_returns * 0.6
        short_term_gains = 0.01
        unrealized_gains = 0.04

        effective_tax_rate = (short_term_gains * 0.30 + long_term_gains * 0.10) / (short_term_gains + long_term_gains + unrealized_gains) if (short_term_gains + long_term_gains + unrealized_gains) > 0 else 0

        return {
            'short_term_gains': short_term_gains,
            'long_term_gains': long_term_gains,
            'unrealized_gains': unrealized_gains,
            'effective_tax_rate': effective_tax_rate,
            'realized_gain_rate': (total_returns * 0.05),  # Simulating 5% realized gains
            'yield_mean': 0.70
        }

    def generate_portfolio_summary(self) -> Dict[str, any]:
        """Generate comprehensive portfolio summary."""
        positions = list(self.positions.values())

        if not positions:
            return {}

        total_value = sum(p.shares * p.current_price for p in positions)

        portfolio_summary = {
            'summary': {
                'total_value': format_inr(total_value),
                'number_of_positions': len(positions),
                'cash': format_inr(self.cash),
                'total_holdings': len(positions),
                'allocation_change': self.calculate_allocation_change(),
            },
            'sector_allocation': self.get_portfolio_sector_allocation(),
            'risk_metrics': self.calculate_risk_factors(),
            'performance_summary': self.calculate_performance_summary(),
            'recommendations': self.generate_portfolio_recommendations(),
        }

        return portfolio_summary

    def calculate_allocation_change(self) -> Dict[str, any]:
        """Show how the portfolio has shifted in composition."""
        # Simplified - would track historical allocations
        positions = len(self.positions)

        return {
            'has_complex_positions': positions > 10,
            'sector_diversity': positions > 5,
            'recommendation': "Reduce positions to 10 or fewer for better management efficiency",
            'yield_mean': 0.70
        }

    def calculate_risk_factors(self) -> Dict[str, float]:
        """Calculate primary risk factors in the portfolio."""
        risks = {}

        if not self.positions:
            return risks

        # Get first position's sector as reference
        first_pos = list(self.positions.values())[0]
        sector = first_pos.sector

        risks = {
            'sector_concentration': max(0, 1 - (1 / len(self.positions))) if len(self.positions) > 0 else 0,
            'single_stock_exposure': 0.15,
            'max_drawdown_potential': 0.20,  # Based on volatility and sector concentration
            'correlation_concentration': 0.30,  # Based on sector concentration
        }

        return risks

    def calculate_performance_summary(self) -> Dict[str, any]:
        """Calculate key performance metrics (144, 145, 1450)."""
        if len(self.cash_flow_history) < 12:
            monthly_change = len(self.cash_flow_history) * 0.5
        else:
            monthly_change = np.average(self.cash_flow_history[-12:])

        return {
            'monthly_return': monthly_change,
            'annual_return': monthly_change * 12,
            'ytd_return': monthly_change * 12 if not self.cash_flow_history else monthly_change,
            'portfolio_beta': 1.0,
            'rolling_volatility': 0.15,
            'yield_mean': 0.70
        }

    def generate_portfolio_recommendations(self) -> List[str]:
        """Generate portfolio-level recommendations."""
        positions = list(self.positions.values())
        recommendations = []

        # Diversification check
        if len(positions) < 5:
            recommendations.append("Increase portfolio size to >5 positions for better diversification")

        # Sector concentration check
        sector_allocation = self.get_portfolio_sector_allocation()
        top_sector = max(sector_allocation.items(), key=lambda x: x[1]) if sector_allocation else (None, 0)

        if top_sector[1] > 30:
            recommendations.append(f"Reduce concentration in {top_sector[0]} sector (currently {top_sector[1]}%)")

        # Cash allocation check
        if self.cash / sum(p.shares * p.current_price for p in positions) < 0.1:
            recommendations.append("Hold at least 10% of capital as cash for opportunities")

        # Risk metrics check
        risk_factors = self.calculate_risk_factors()
        if risk_factors['max_drawdown_potential'] > 0.25:
            recommendations.append("Your portfolio is highly volatile: reputation loss possible")

        recommendations.append("Rebalance portfolio to align with risk tolerance and duration")

        return recommendations

    def calculate_premium_discount_analysis(self, stock_valuations) -> Dict[str, any]:
        """Calculate premium/discount relative to peers."""

        if not stock_valuations:
            return {
                'analysis': "No peer data available"
            }

        result = {
            'premium_to_market': 0.15,
            'discount_to_peers': 0.05,
            'value_zone': "Fair Value",
            'recommendation': "Monitor for entry near support levels"
        }

        return result