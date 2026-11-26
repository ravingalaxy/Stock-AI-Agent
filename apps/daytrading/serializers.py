"""REST API serializers for Day Trading models."""

from rest_framework import serializers
from .models import (
    DayTradePlan, PaperOrder, PaperPosition, PaperFill,
    TradingAlert, ScanResult, NewsItem, BacktestScenario,
    PublicDisclosure, TradeJournalEntry, PaperAccount,
)


class ScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanResult
        fields = '__all__'


class NewsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = '__all__'


class DayTradePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayTradePlan
        fields = '__all__'


class PaperOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperOrder
        fields = '__all__'
        read_only_fields = ('is_paper',)


class PaperPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperPosition
        fields = '__all__'
        read_only_fields = ('is_paper',)


class PaperFillSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperFill
        fields = '__all__'


class TradingAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingAlert
        fields = '__all__'


class BacktestScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestScenario
        fields = '__all__'


class PublicDisclosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicDisclosure
        fields = '__all__'


class TradeJournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeJournalEntry
        fields = '__all__'


class PaperAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperAccount
        fields = '__all__'
        read_only_fields = ('is_paper',)


class SubmitOrderSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=30)
    side = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    order_type = serializers.ChoiceField(choices=["MARKET", "LIMIT", "SL", "SL_LIMIT"], default="MARKET")
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    trigger_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    product = serializers.ChoiceField(choices=["MIS", "CNC"], default="MIS")
    exchange = serializers.ChoiceField(choices=["NSE", "BSE"], default="NSE")


class CreateAlertSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=30)
    alert_type = serializers.ChoiceField(choices=[
        "PRICE_ABOVE", "PRICE_BELOW", "VOLUME_SPIKE", "BREAKOUT",
        "ENTRY_SIGNAL", "EXIT_SIGNAL", "STOP_LOSS_HIT", "NEWS",
    ])
    condition = serializers.CharField(max_length=255)
    threshold = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)


class BacktestRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=30)
    strategy = serializers.ChoiceField(choices=["ORB", "MOMENTUM", "BREAKOUT"], default="ORB")
    lookback_days = serializers.IntegerField(min_value=5, max_value=180, default=60)
    exchange = serializers.ChoiceField(choices=["NSE", "BSE"], default="NSE")
