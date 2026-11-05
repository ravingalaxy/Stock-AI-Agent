# Suppress Pandas4Warning from yfinance (pandas >= 3.1 deprecation warnings).
# pandas 3.1 uses warnings.warn_explicit which bypasses filterwarnings/simplefilter,
# so we intercept at the showwarning level to prevent stderr spam.
import warnings

_original_showwarning = warnings.showwarning

def _filtered_showwarning(message, category, filename, lineno, file=None, line=None):
    if category.__name__ == "Pandas4Warning":
        return  # silently drop
    _original_showwarning(message, category, filename, lineno, file, line)

warnings.showwarning = _filtered_showwarning


# Enable SQLite WAL mode for concurrent read/write support.
# This prevents "database is locked" errors when multiple requests hit the DB.
from django.db.backends.signals import connection_created

def _activate_wal_mode(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.execute("PRAGMA cache_size=-64000;")

connection_created.connect(_activate_wal_mode)
