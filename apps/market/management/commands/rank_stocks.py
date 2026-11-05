from django.core.management.base import BaseCommand
from apps.market.models import Stock, AgentEvaluation
from apps.market.services import seed_universe_if_empty


class Command(BaseCommand):
    help = "Executes multi-factor ranking algorithm on the active universe."

    def handle(self, *args, **options):
        seed_universe_if_empty()
        evals = AgentEvaluation.objects.all().order_by('rank')
        self.stdout.write(self.style.SUCCESS(f"Rankings calculated for {evals.count()} equities:"))
        for ev in evals[:10]:
            self.stdout.write(f"#{ev.rank:>2} | {ev.stock.symbol:<14} | Score: {ev.composite_score:>4.1f} | Action: {ev.action}")
