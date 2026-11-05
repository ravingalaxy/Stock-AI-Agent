"""Institutional-Grade DCF and Multi-Model Valuation Engine."""

import math
import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

from src.utils.logger import logger
from src.utils.helpers import format_inr, format_percentage, safe_divide


@dataclass
class DCFParameters:
    """Parameters for DCF valuation."""
    current_fcf_per_share: float = 0.0     # Latest Free Cash Flow per share (INR)
    fcf_cagr: float = 0.12                 # Expected FCF CAGR for explicit forecast period (5 years)
    terminal_growth_rate: float = 0.03      # Long-term terminal growth rate (typically 2.5% - 4.0% for India)
    wacc: float = 0.11                      # Weighted Average Cost of Capital (typically 10% - 13% for Indian equities)
    forecast_years: int = 5                 # High growth stage duration
    transition_years: int = 5               # Fade period duration towards terminal growth
    cash_per_share: float = 0.0             # Cash and cash equivalents per share
    debt_per_share: float = 0.0             # Total debt per share
    net_debt_per_share: float = 0.0         # Net debt per share
    current_price: Optional[float] = None   # Current market price for margin of safety calculation
    eps: Optional[float] = None             # Trailing EPS for Graham & Lynch models
    book_value_per_share: Optional[float] = None # BVPS for Graham model


class DCFValuator:
    """Discounted Cash Flow & Intrinsic Valuation Model for NSE/BSE securities."""

    def __init__(self, company_name: str = "Company"):
        self.company_name = company_name
        self.results: Dict[str, Any] = {}

    def calculate_dcf(self, parameters: DCFParameters) -> Dict[str, Any]:
        """
        Calculate institutional 2-stage DCF intrinsic value with fade period.

        Stage 1: High growth explicit forecast (Years 1 to forecast_years)
        Stage 2: Fade transition period (Years forecast_years+1 to 10) linearly fading to terminal growth
        Stage 3: Terminal Value via Gordon Growth Model with net debt adjustment
        """
        self.results = {}

        try:
            fcf_base = parameters.current_fcf_per_share
            wacc = max(parameters.wacc, 0.05)  # Enforce reasonable floor for discount rate
            g_terminal = min(parameters.terminal_growth_rate, wacc - 0.015)  # Enforce minimum spread of 1.5%

            # Explicit Forecast Stage
            fcfs: List[float] = []
            growth_rates: List[float] = []
            current_fcf = fcf_base

            # Phase 1: High growth years
            for year in range(1, parameters.forecast_years + 1):
                growth = parameters.fcf_cagr
                growth_rates.append(growth)
                current_fcf = current_fcf * (1.0 + growth)
                fcfs.append(current_fcf)

            # Phase 2: Fade years towards terminal growth
            for step in range(1, parameters.transition_years + 1):
                weight = step / (parameters.transition_years + 1)
                faded_growth = (1.0 - weight) * parameters.fcf_cagr + weight * g_terminal
                growth_rates.append(faded_growth)
                current_fcf = current_fcf * (1.0 + faded_growth)
                fcfs.append(current_fcf)

            total_years = len(fcfs)

            # Discount explicit and transition FCFs
            pv_fcfs = [
                fcf / ((1.0 + wacc) ** (t + 1))
                for t, fcf in enumerate(fcfs)
            ]
            sum_pv_fcfs = sum(pv_fcfs)

            # Terminal Value Calculation (Gordon Growth Model at Year 10)
            terminal_fcf = fcfs[-1] * (1.0 + g_terminal)
            terminal_spread = max(wacc - g_terminal, 0.015)
            terminal_value = terminal_fcf / terminal_spread
            pv_terminal_value = terminal_value / ((1.0 + wacc) ** total_years)

            # Operating Value per Share
            operating_value_per_share = sum_pv_fcfs + pv_terminal_value

            # Net Debt Adjustment per share
            net_cash_per_share = parameters.cash_per_share - parameters.debt_per_share
            intrinsic_value_per_share = max(operating_value_per_share + net_cash_per_share, 0.0)

            # Valuation metrics and Margin of Safety
            curr_p = parameters.current_price or 0.0
            margin_of_safety = 0.0
            upside_pct = 0.0
            if curr_p > 0 and intrinsic_value_per_share > 0:
                upside_pct = ((intrinsic_value_per_share - curr_p) / curr_p) * 100.0
                margin_of_safety = ((intrinsic_value_per_share - curr_p) / intrinsic_value_per_share) * 100.0

            # Sensitivity Grid: WACC vs Terminal Growth
            sensitivity = self.generate_sensitivity_matrix(parameters)

            # Multi-Model Comparables
            graham_val = self.calculate_graham_number(parameters.eps, parameters.book_value_per_share)
            lynch_val = self.calculate_peter_lynch_fair_value(parameters.eps, parameters.fcf_cagr)

            valuation = {
                'current_fcf_per_share': parameters.current_fcf_per_share,
                'projected_fcfs': [round(x, 2) for x in fcfs],
                'projected_growths': [round(g * 100, 1) for g in growth_rates],
                'discounted_fcfs': [round(x, 2) for x in pv_fcfs],
                'pv_explicit_fcfs': round(sum_pv_fcfs, 2),
                'terminal_value': round(terminal_value, 2),
                'pv_terminal_value': round(pv_terminal_value, 2),
                'terminal_value_weight_pct': round(safe_divide(pv_terminal_value, operating_value_per_share) * 100, 1),
                'operating_value_per_share': round(operating_value_per_share, 2),
                'net_cash_per_share': round(net_cash_per_share, 2),
                'intrinsic_value_per_share': round(intrinsic_value_per_share, 2),
                'intrinsic_value': round(intrinsic_value_per_share, 2),
                'pv_forecast_sum': round(sum_pv_fcfs, 2),
                'current_price': curr_p,
                'margin_of_safety_pct': round(margin_of_safety, 1),
                'upside_potential_pct': round(upside_pct, 1),
                'valuation_verdict': "Undervalued" if upside_pct > 15 else ("Fairly Valued" if upside_pct >= -10 else "Overvalued"),
                'sensitivity_matrix': sensitivity,
                'graham_number': round(graham_val, 2) if graham_val else None,
                'peter_lynch_value': round(lynch_val, 2) if lynch_val else None
            }

            self.results = valuation
            return valuation

        except Exception as e:
            logger.error(f"DCF calculation error for {self.company_name}: {e}")
            self.results = {'error': str(e), 'intrinsic_value_per_share': 0.0}
            return self.results

    def generate_sensitivity_matrix(self, parameters: DCFParameters) -> Dict[str, Any]:
        """Generate a 2D matrix of intrinsic values across WACC and Terminal Growth."""
        wacc_range = [0.09, 0.10, 0.11, 0.12, 0.13, 0.14]
        g_range = [0.020, 0.025, 0.030, 0.035, 0.040]
        
        matrix = []
        for w in wacc_range:
            row = []
            for g in g_range:
                if w <= g + 0.005:
                    row.append(None)
                    continue
                # Fast DCF approximation
                fcf = parameters.current_fcf_per_share
                pv_f = sum(
                    (fcf * ((1 + parameters.fcf_cagr) ** (t + 1))) / ((1 + w) ** (t + 1))
                    for t in range(5)
                )
                fcf_5 = fcf * ((1 + parameters.fcf_cagr) ** 5)
                tv = (fcf_5 * (1 + g)) / (w - g)
                pv_tv = tv / ((1 + w) ** 5)
                val = pv_f + pv_tv + (parameters.cash_per_share - parameters.debt_per_share)
                row.append(round(max(val, 0.0), 1))
            matrix.append(row)

        return {
            "wacc_labels": [f"{int(w * 100)}%" for w in wacc_range],
            "growth_labels": [f"{g * 100:.1f}%" for g in g_range],
            "values": matrix
        }

    @staticmethod
    def calculate_graham_number(eps: Optional[float], bvps: Optional[float]) -> Optional[float]:
        """Ben Graham Number = sqrt(22.5 * EPS * BVPS)."""
        if eps is None or bvps is None or eps <= 0 or bvps <= 0:
            return None
        return math.sqrt(22.5 * eps * bvps)

    @staticmethod
    def calculate_peter_lynch_fair_value(eps: Optional[float], growth_rate: float) -> Optional[float]:
        """Peter Lynch Fair Value = EPS * (Growth Rate % capped at 30%)."""
        if eps is None or eps <= 0:
            return None
        g_pct = min(max(growth_rate * 100, 5.0), 30.0)
        return eps * g_pct

    def generate_report(self, parameters: DCFParameters) -> str:
        """Generate human-friendly DCF quantitative report."""
        val = self.calculate_dcf(parameters)
        if "error" in val:
            return f"# Valuation Report: {val['error']}"

        return f"""
# Institutional DCF Valuation: {self.company_name}
- **Current Market Price**: {format_inr(parameters.current_price or 0)}
- **Intrinsic Value per Share**: {format_inr(val['intrinsic_value_per_share'])}
- **Upside / Downside**: {val['upside_potential_pct']:+.1f}%
- **Margin of Safety**: {val['margin_of_safety_pct']:.1f}%
- **Verdict**: **{val['valuation_verdict']}**
- **WACC**: {parameters.wacc*100:.1f}% | **Terminal Growth**: {parameters.terminal_growth_rate*100:.1f}%
- **PV of 10-Yr Cash Flows**: {format_inr(val['pv_explicit_fcfs'])}
- **PV of Terminal Value**: {format_inr(val['pv_terminal_value'])} ({val['terminal_value_weight_pct']}% of Enterprise Value)
- **Graham Number**: {format_inr(val['graham_number']) if val.get('graham_number') else 'N/A'}
- **Peter Lynch Fair Value**: {format_inr(val['peter_lynch_value']) if val.get('peter_lynch_value') else 'N/A'}
"""
