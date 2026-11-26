"""Indian securities transaction charges calculator.

Covers: Brokerage, STT, Exchange Txn Charges, GST, SEBI Turnover Fee, Stamp Duty.
All in INR. Rates as of 2024-25.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

BROKERAGE_FLAT = Decimal("20.00")
STT_RATE_INTRADAY_SELL = Decimal("0.000250")
STT_RATE_DELIVERY = Decimal("0.001000")
EXCHANGE_TXN_NSE = Decimal("0.0000297")
EXCHANGE_TXN_BSE = Decimal("0.0000030")
SEBI_TURNOVER_FEE = Decimal("0.000001")
GST_RATE = Decimal("0.18")
STAMP_DUTY_INTRADAY = Decimal("0.00003")
STAMP_DUTY_DELIVERY = Decimal("0.00015")


def calculate_charges(turnover, side, product="MIS", exchange="NSE",
                      brokerage_per_order=BROKERAGE_FLAT):
    """Calculate all charges for a single leg."""
    turnover = Decimal(str(turnover))
    is_buy = side.upper() == "BUY"
    is_intraday = product.upper() == "MIS"
    r2 = Decimal("0.01")

    brokerage = min(brokerage_per_order, turnover * Decimal("0.0003")).quantize(r2, ROUND_HALF_UP)

    if is_intraday:
        stt = (turnover * STT_RATE_INTRADAY_SELL).quantize(r2, ROUND_HALF_UP) if not is_buy else Decimal("0")
    else:
        stt = (turnover * STT_RATE_DELIVERY).quantize(r2, ROUND_HALF_UP)

    exc_rate = EXCHANGE_TXN_NSE if exchange.upper() == "NSE" else EXCHANGE_TXN_BSE
    exchange_charges = (turnover * exc_rate).quantize(r2, ROUND_HALF_UP)
    sebi_fee = (turnover * SEBI_TURNOVER_FEE).quantize(Decimal("0.0001"), ROUND_HALF_UP)
    gst = ((brokerage + exchange_charges) * GST_RATE).quantize(r2, ROUND_HALF_UP)

    if is_buy:
        sd_rate = STAMP_DUTY_INTRADAY if is_intraday else STAMP_DUTY_DELIVERY
        stamp_duty = (turnover * sd_rate).quantize(r2, ROUND_HALF_UP)
    else:
        stamp_duty = Decimal("0")

    total = brokerage + stt + exchange_charges + sebi_fee + gst + stamp_duty
    return {
        "brokerage": brokerage, "stt": stt, "exchange_charges": exchange_charges,
        "sebi_fee": sebi_fee, "gst": gst, "stamp_duty": stamp_duty,
        "total": total.quantize(r2, ROUND_HALF_UP),
    }


def round_trip_charges(buy_price, sell_price, quantity, product="MIS", exchange="NSE"):
    """Total charges for a complete buy-then-sell round trip."""
    buy_turnover = Decimal(str(buy_price)) * quantity
    sell_turnover = Decimal(str(sell_price)) * quantity
    buy_ch = calculate_charges(buy_turnover, "BUY", product, exchange)
    sell_ch = calculate_charges(sell_turnover, "SELL", product, exchange)
    combined = {}
    for key in buy_ch:
        combined[key] = buy_ch[key] + sell_ch[key]
    combined["buy_charges"] = buy_ch["total"]
    combined["sell_charges"] = sell_ch["total"]
    return combined
