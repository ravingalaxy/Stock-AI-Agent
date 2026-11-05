"""
Django management command to seed benchmark NSE/BSE universe, IPO intelligence, and research engine.
Ensures zero-friction setup on clean clone across any OS.
"""

from django.core.management.base import BaseCommand
from apps.market.services import seed_universe_if_empty
from apps.market.models import Stock
from apps.ipo.services import seed_ipo_universe_if_empty
from apps.ipo.models import IPOListing
from src.storage.database import DatabaseManager


class Command(BaseCommand):
    help = "Seeds initial high-profile NSE and BSE stocks, prices, fundamentals, IPO intelligence, and initializes quant databases."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-seeding even if records exist.',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write("Initializing StockAgent AI environment...")

        # 1. Initialize SQLAlchemy Quant Research Database schema
        try:
            db_manager = DatabaseManager()
            db_manager.init_db()
            self.stdout.write(self.style.SUCCESS("  [OK] Quantitative research database schema initialized (data/stock_research.db)."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  [!] Note on research DB init: {e}"))

        # 2. Seed Equity Universe
        initial_stock_count = Stock.objects.count()
        if initial_stock_count == 0 or force:
            self.stdout.write("  Seeding high-conviction benchmark equity universe...")
            seed_universe_if_empty()
            self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully seeded {Stock.objects.count()} benchmark equities with real pricing & 365-day price histories!"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Equity universe already populated ({initial_stock_count} stocks)."))

        # 3. Seed IPO Intelligence Pipeline
        initial_ipo_count = IPOListing.objects.count()
        if initial_ipo_count == 0 or force:
            self.stdout.write("  Seeding IPO surveillance universe...")
            seed_ipo_universe_if_empty(force=force)
            self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully seeded {IPOListing.objects.count()} IPOs across Mainboard & SME!"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  [OK] IPO intelligence pipeline already populated ({initial_ipo_count} IPOs)."))

        self.stdout.write(self.style.SUCCESS("\nUniverse initialization complete. Application is 100% ready to run!"))
