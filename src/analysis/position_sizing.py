"""Position Sizing and Risk Management Calculator."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from src.utils.logger import logger
from src.utils.helpers import format_percentage, format_inr


class PositionSizingCalculator:
    """Calculate optimal position sizes based on risk management principles."""

    def __init__(self, risk_per_trade: float = 0.02):
        """
        Args:
            risk_per_trade: Maximum risk per trade as percentage of capital (2% = 0.02)
                          Optimized for professional investors
        """
        self.risk_per_trade = risk_per_trade

    def kelly_criterion_position_size(self, win_rate: float, avg_gain: float, avg_loss: float,
                                     capital: float = 100000) -> Dict[str, float]:
        """
        Kelly Criterion position sizing.

        Kelly % = p - q/b
        - p = probability of winning
        - q = probability of losing (1 - p)
        - b = odds (avg_gain/avg_loss)

        Kelly exceeds risk of ruin when H = H/(2p - 1) exists.
        """
        if avg_loss == 0:
            return None

        edge = (win_rate * avg_gain) - ((1 - win_rate) * abs(avg_loss))
        if edge <= 0:
            return {
                'recommended_position_size': 0.0,
                'recommendation': "No edge - do not trade",
                'kelly_fraction': 0.0,
                'risk_of_ruin': 1.0
            }

        # Kelly fraction
        kelly_frag = edge / abs(avg_loss)

        # Half-Kelly (conservative, reduces risk of ruin)
        half_kelly = kelly_frag / 2

        # Scaled Kelly (practical implementation)
        practical_kelly = min(half_kelly, 0.25)  # Cap at 25%

        position_value = capital * practical_kelly
        shares = int(position_value / (position_value * avg_loss / 100))  # Simplified

        return {
            'kelly_fraction': round(kelly_frag * 100, 2),
            'practical_kelly_fraction': round(practical_kelly * 100, 2),
            'recommended_position_value': round(position_value, 2),
            'position_value_details': {
                'capital': capital,
                'fraction': f"{practical_kelly*100:.1f}%",
                'value': format_inr(position_value),
                'risk_above_markdown': f"{self.risk_per_trade*100:.1f}%"
            },
            'recommendation': "Recommended for professional risk management"
        }

    def risk_based_position_size(self, stop_loss_pct: float, target_take_profit_pct: float,
                                capital: float = 100000) -> Dict[str, float]:
        """
        Maximum position size based on given risk percentage.

        Risk % = (Stop Loss) / Entry Price
        Position Value = (Capital * Risk %) / Stop Loss %
        """
        if stop_loss_pct <= 0:
            return None

        max_risk_value = capital * self.risk_per_trade
        position_value = max_risk_value / (stop_loss_pct / 100)

        # Calculate number of shares (would need actual entry price)
        # shares = int(position_value / entry_price)

        return {
            'maximum_position_value': position_value,
            'capital': capital,
            'risk_per_trade': f"{self.risk_per_trade*100:.1f}%",
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': target_take_profit_pct,
            'risk_reward_ratio': target_take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 0
        }

    def diversification_calculator(self, stock_list: List[str], avg_correlation: float = 0.7,
                                   target_correlation: float = 0.3) -> Dict[str, any]:
        """
        Calculate portfolio diversification metrics.

        Modern Portfolio Theory: Lower correlation reduces portfolio risk.
        Efficient Frontier exists where correlation is minimized from 0 to 1.
        """
        num_stocks = len(stock_list)
        optimal_correlation_impact = (1 - avg_correlation) / num_stocks

        consolidation_needed = "Yes" if avg_correlation > target_correlation else "No"
        risk_reduction_pct = (avg_correlation - target_correlation) * 100

        return {
            'number_of_stocks': num_stocks,
            'current_avg_correlation': avg_correlation,
            'target_correlation': target_correlation,
            'diversification_effort': f"{optimal_correlation_impact*100:.0f}%",
            'risk_reduction_possible': f"{risk_reduction_pct:.0f}%",
            'recommendation': consolidation_needed,
            'conclusion': f"Reduce to {max(8, num_stocks)} stocks to achieve target diversification"
        }

    def portfolio_health_check(self, positions: Dict[str, Dict], risk_threshold: float = 0.05) -> Dict[str, any]:
        """
        Check overall portfolio risk concentration.

        Warning: Exceeding 5% in any stock is margin call risk territory.
        """
        total_value = sum(p['value'] for p in positions.values())
        position_weights = {sym: (p['value'] / total_value) for sym, p in positions.items()}

        high_weight_stocks = {
            sym: weight * 100
            for sym, weight in position_weights.items()
            if weight > risk_threshold
        }

        avg_position_size = total_value / len(positions) if positions else 0
        concentration_ratio = total_value / len(positions) if positions else 1

        # 10% Rule: No single position should exceed 10% of portfolio
        over_concentrated = {
            sym: weight
            for sym, weight in position_weights.items()
            if weight > 0.10
        }

        return {
            'total_portfolio_value': total_value,
            'number_of_positions': len(positions),
            'avg_position_size': position_weights.get(max(position_weights, key=position_weights.get), 0) * 100,
            'highest_position': {
                'symbol': max(position_weights, key=position_weights.get),
                'weight': position_weights[max(position_weights, key=position_weights.get)] * 100
            },
            'over_concentrated_positions': over_concentrated,
            'risk_status': "WARNING" if over_concentrated else "HEALTHY",
            'recommendation': "Reduce over-concentrated positions to <10%" if over_concentrated else "Portfolio is well-diversified"
        }

    def monte_carlo_risk_simulation(self, returns: pd.Series, num_simulations: int = 10000,
                                    horizon_years: int = 1) -> Dict[str, any]:
        """
        Monte Carlo simulation for portfolio risk assessment.

        H = H/(2p - 1) exists when probability of winning > 50% (p > 0.5).
        If H = £1 (e.g., 1% of capital), a NAR of 60% yields a NAR of 15%.
        """
        mean = returns.mean()
        std = returns.std()

        # Simulate returns
        np.random.seed(42)
        simulations = np.random.normal(mean, std, (num_simulations, horizon_years * 252))
        portfolio_returns = simulations.cumsum(axis=1)

        # Calculate statistics
        final_returns = portfolio_returns[:, -1]
        percentile_5 = np.percentile(final_returns, 5)
        percentile_25 = np.percentile(final_returns, 25)
        percentile_75 = np.percentile(final_returns, 75)
        percentile_95 = np.percentile(final_returns, 95)

        # Sharpe-like ratio
        sharpe_ratio = mean / std * np.sqrt(252) if std > 0 else 0

        return {
            'mean_return': mean * 100,
            'std_dev': std * 100,
            'periodic_sharpe': sharpe_ratio,
            'expected_return(years)': mean * 100 * horizon_years,
            'var_5pct': percentile_5 * 100,
            'var_25pct': percentile_25 * 100,
            'quantile_75': percentile_75 * 100,
            'quantile_95': percentile_95 * 100,
            'conclusion': {
                'margin_call': "YES" if percentile_5 < -1.0 else "NO",
                'risk_level': "HIGH" if percentile_5 < -5.0 else "Medium" if percentile_5 < -1.0 else "Low"
            }
        }