"""
Universal Portfolio Statement Parser.
Extracts equity holdings, transactions, and statement metadata from CSV, Excel (XLSX, XLS),
PDF, and DOCX files. Supports major Indian brokers (FYERS, Zerodha, Upstox, Groww, Angel One,
ICICI Direct) and generic brokerage holding statements.
"""

import io
import re
import csv
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, BinaryIO
from dataclasses import dataclass, field, asdict

import pandas as pd

from src.utils.logger import logger


@dataclass
class ParsedHolding:
    """Standardized holding record extracted from a portfolio statement."""
    stock_name: str
    symbol: str
    clean_symbol: str
    exchange: str
    isin: str
    quantity: float
    buy_price: float
    current_price: float
    invested_amount: float
    current_value: float
    pnl_amount: float
    pnl_pct: float
    sector: str = "Not available in uploaded file"
    industry: str = "Not available in uploaded file"
    statement_date: str = "Not available in uploaded file"
    raw_symbol: str = ""
    is_enriched: bool = False
    validation_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedPortfolio:
    """Complete portfolio statement extraction output."""
    filename: str
    file_type: str
    statement_date: str
    client_name: str
    client_id: str
    reported_invested: Optional[float]
    reported_current: Optional[float]
    reported_pnl: Optional[float]
    holdings: List[ParsedHolding] = field(default_factory=list)
    raw_headers: List[str] = field(default_factory=list)
    detected_column_map: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return len(self.holdings) > 0 and len(self.errors) == 0

    @property
    def total_invested_calculated(self) -> float:
        return sum(h.invested_amount for h in self.holdings)

    @property
    def total_current_calculated(self) -> float:
        return sum(h.current_value for h in self.holdings)

    @property
    def total_pnl_calculated(self) -> float:
        return self.total_current_calculated - self.total_invested_calculated

    @property
    def total_pnl_pct_calculated(self) -> float:
        if self.total_invested_calculated > 0:
            return (self.total_pnl_calculated / self.total_invested_calculated) * 100.0
        return 0.0


class PortfolioParser:
    """Institutional-grade file parser for Indian broker statements."""

    # Canonical column matching patterns (regex or substrings)
    COLUMN_PATTERNS = {
        "symbol": [
            r"^symbol$", r"^stock\s*symbol$", r"^ticker$", r"^instrument$",
            r"^scrip\s*name$", r"^name$", r"^trading\s*symbol$", r"^scrip$"
        ],
        "name": [
            r"^company\s*name$", r"^stock\s*name$", r"^security\s*name$",
            r"^company$", r"^description$", r"^particulars$"
        ],
        "isin": [
            r"^isin$", r"^isin\s*code$", r"^isin\s*number$"
        ],
        "quantity": [
            r"^qty$", r"^quantity$", r"^shares$", r"^units$", r"^qty\.$",
            r"^holding\s*qty$", r"^available\s*qty$", r"^total\s*qty$"
        ],
        "buy_price": [
            r"^buy\s*price$", r"^avg\.?\s*cost$", r"^avg\.?\s*price$",
            r"^average\s*buy\s*price$", r"^buy\s*avg$", r"^cost\s*price$",
            r"^average\s*cost$", r"^purchase\s*price$"
        ],
        "current_price": [
            r"^current\s*price$", r"^ltp$", r"^cmp$", r"^market\s*price$",
            r"^cur\.?\s*price$", r"^last\s*price$", r"^close\s*price$",
            r"^previous\s*close$"
        ],
        "invested_amount": [
            r"^invested\s*value$", r"^invested\s*amount$", r"^total\s*cost$",
            r"^cost\s*value$", r"^invested$", r"^total\s*investment$"
        ],
        "current_value": [
            r"^current\s*value$", r"^cur\.?\s*val$", r"^market\s*value$",
            r"^present\s*value$", r"^cur\.?\s*value$"
        ],
        "pnl_amount": [
            r"^unrealised\s*p&l$", r"^unrealized\s*p&l$", r"^profit\s*&\s*loss$",
            r"^p&l$", r"^unrealised\s*profit$", r"^total\s*p&l$", r"^gain/loss$"
        ],
        "pnl_pct": [
            r"^unrealised\s*p&l\s*%$", r"^unrealized\s*p&l\s*%$", r"^p&l\s*%$",
            r"^returns\s*%$", r"^net\s*chg\.?\s*%$", r"^percentage\s*gain$",
            r"^gain/loss\s*%$", r"^chg\s*%$"
        ],
        "sector": [
            r"^sector$", r"^industry$", r"^category$"
        ]
    }

    @classmethod
    def clean_number(cls, val: Any) -> float:
        """Parses float from numbers with commas, currency symbols, and negative formats."""
        if val is None or val == "" or pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)

        s = str(val).strip()
        # Handle parentheses for negatives e.g. (1,234.50)
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1]
        elif s.startswith("-"):
            is_negative = True
            s = s[1:]

        # Remove commas, currency symbols, and whitespace
        s = re.sub(r"[₹$,\s%]", "", s)
        try:
            val_flt = float(s)
            return -val_flt if is_negative else val_flt
        except ValueError:
            return 0.0

    @classmethod
    def parse_exchange_and_symbol(cls, raw: str) -> tuple[str, str, str]:
        """
        Extracts (exchange, clean_symbol, raw_symbol) from broker string.
        Examples:
          'NSE:IDEA-EQ' -> ('NSE', 'IDEA', 'IDEA.NS')
          'BSE:MISHTANN-T' -> ('BSE', 'MISHTANN', 'MISHTANN.BO')
          'RELIANCE.NS' -> ('NSE', 'RELIANCE', 'RELIANCE.NS')
          'TCS' -> ('NSE', 'TCS', 'TCS.NS')
        """
        raw_str = str(raw).strip()
        exchange = "NSE"

        # Check prefix e.g. NSE: or BSE:
        prefix_match = re.match(r"^(NSE|BSE)\s*:\s*(.*)$", raw_str, re.IGNORECASE)
        if prefix_match:
            exchange = prefix_match.group(1).upper()
            inner = prefix_match.group(2).strip()
        else:
            inner = raw_str

        # Remove series suffix e.g. -EQ, -T, -B, -X, -Z, -SM, -BE, -BL
        series_match = re.match(r"^(.*?)-(EQ|T|B|X|Z|SM|BE|BL|BZ|E1)$", inner, re.IGNORECASE)
        if series_match:
            clean = series_match.group(1).strip()
        else:
            clean = inner

        # Remove existing .NS or .BO suffix
        if clean.upper().endswith(".NS"):
            clean = clean[:-3]
            exchange = "NSE"
        elif clean.upper().endswith(".BO"):
            clean = clean[:-3]
            exchange = "BSE"

        clean = clean.upper().strip()
        yahoo_symbol = f"{clean}.NS" if exchange == "NSE" else f"{clean}.BO"
        return exchange, clean, yahoo_symbol

    @classmethod
    def detect_file_type(cls, file_input: Union[str, Path, BinaryIO], filename: str = "") -> str:
        """Identifies file format from extension and content headers."""
        fname = str(filename or getattr(file_input, "name", "") or file_input).lower()
        if fname.endswith(".csv"):
            return "csv"
        elif fname.endswith(".xlsx"):
            return "xlsx"
        elif fname.endswith(".xls"):
            return "xls"
        elif fname.endswith(".pdf"):
            return "pdf"
        elif fname.endswith(".docx"):
            return "docx"

        # Fallback to magic bytes check if available
        if hasattr(file_input, "read") and hasattr(file_input, "seek"):
            head = file_input.read(8)
            file_input.seek(0)
            if head.startswith(b"%PDF"):
                return "pdf"
            elif head.startswith(b"PK\x03\x04"):
                return "xlsx"  # or docx
            elif head.startswith(b"\xd0\xcf\x11\xe0"):
                return "xls"

        return "csv"

    @classmethod
    def parse_file(
        cls,
        file_input: Union[str, Path, BinaryIO, bytes],
        filename: str = "",
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedPortfolio:
        """Universal entry point to parse any portfolio file."""
        if isinstance(file_input, (str, Path)):
            path = Path(file_input)
            fname = filename or path.name
            with open(path, "rb") as f:
                content = f.read()
        elif isinstance(file_input, bytes):
            content = file_input
            fname = filename or "portfolio_upload.csv"
        else:
            fname = filename or getattr(file_input, "name", "uploaded_statement")
            content = file_input.read()

        file_type = cls.detect_file_type(fname)
        logger.info(f"Parsing portfolio statement: {fname} (detected type: {file_type})")

        try:
            if file_type == "csv":
                return cls._parse_csv(content, fname, custom_mapping)
            elif file_type in ["xlsx", "xls"]:
                return cls._parse_excel(content, fname, file_type, custom_mapping)
            elif file_type == "pdf":
                return cls._parse_pdf(content, fname, custom_mapping)
            elif file_type == "docx":
                return cls._parse_docx(content, fname, custom_mapping)
            else:
                parsed = ParsedPortfolio(
                    filename=fname,
                    file_type="unknown",
                    statement_date="Not available in uploaded file",
                    client_name="Not available in uploaded file",
                    client_id="Not available in uploaded file",
                    reported_invested=None,
                    reported_current=None,
                    reported_pnl=None,
                )
                parsed.errors.append(f"Unsupported file format for '{fname}'. Please upload CSV, XLSX, XLS, PDF, or DOCX.")
                return parsed
        except Exception as e:
            logger.error(f"Failed to parse portfolio file {fname}: {e}", exc_info=True)
            parsed = ParsedPortfolio(
                filename=fname,
                file_type=file_type,
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            parsed.errors.append(f"Error parsing file '{fname}': {str(e)}")
            return parsed

    @classmethod
    def _parse_csv(
        cls,
        content: bytes,
        filename: str,
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedPortfolio:
        """Parses CSV holding statements with metadata header detection."""
        # Try UTF-8 then Latin-1
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        reader = list(csv.reader(lines))

        metadata = {}
        table_start_idx = -1

        # Scan for metadata in header rows (before main table)
        for idx, row in enumerate(reader):
            if not row:
                continue
            first_cell = row[0].strip().lower()

            # Check if this row is the table header
            if cls._is_table_header(row):
                table_start_idx = idx
                break

            # Key-value metadata extraction
            if len(row) >= 2 and row[0].strip():
                k = row[0].strip()
                v = row[1].strip()
                metadata[k] = v

        if table_start_idx == -1:
            # Fallback: inspect lines for best header match
            for idx, row in enumerate(reader):
                if any(any(re.search(pat, c.strip().lower()) for pat in cls.COLUMN_PATTERNS["symbol"]) for c in row):
                    table_start_idx = idx
                    break

        if table_start_idx == -1:
            res = ParsedPortfolio(
                filename=filename,
                file_type="csv",
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append("Could not locate a valid holdings table header in the CSV statement.")
            return res

        raw_headers = [c.strip() for c in reader[table_start_idx]]
        data_rows = reader[table_start_idx + 1:]

        # Build column map
        col_map = custom_mapping or cls._map_columns(raw_headers)

        return cls._build_parsed_portfolio(
            filename=filename,
            file_type="csv",
            raw_headers=raw_headers,
            col_map=col_map,
            data_rows=data_rows,
            metadata=metadata
        )

    @classmethod
    def _parse_excel(
        cls,
        content: bytes,
        filename: str,
        file_type: str,
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedPortfolio:
        """Parses Excel workbook (.xlsx or .xls)."""
        bio = io.BytesIO(content)
        engine = "openpyxl" if file_type == "xlsx" else "xlrd"

        try:
            excel_file = pd.ExcelFile(bio, engine=engine)
        except Exception as e:
            res = ParsedPortfolio(
                filename=filename,
                file_type=file_type,
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append(f"Failed to open Excel workbook: {e}")
            return res

        # Read first sheet as string table
        sheet_name = excel_file.sheet_names[0]
        df_raw = excel_file.parse(sheet_name, header=None)

        # Convert to list of list of strings
        rows = []
        for _, row in df_raw.iterrows():
            row_vals = ["" if pd.isna(v) else str(v).strip() for v in row.values]
            if any(row_vals):
                rows.append(row_vals)

        metadata = {}
        table_start_idx = -1

        for idx, row in enumerate(rows):
            if cls._is_table_header(row):
                table_start_idx = idx
                break
            if len(row) >= 2 and row[0]:
                metadata[row[0]] = row[1]

        if table_start_idx == -1:
            for idx, row in enumerate(rows):
                if any(any(re.search(pat, c.strip().lower()) for pat in cls.COLUMN_PATTERNS["symbol"]) for c in row):
                    table_start_idx = idx
                    break

        if table_start_idx == -1:
            res = ParsedPortfolio(
                filename=filename,
                file_type=file_type,
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append("Could not locate a valid holdings table in the Excel sheet.")
            return res

        raw_headers = rows[table_start_idx]
        data_rows = rows[table_start_idx + 1:]
        col_map = custom_mapping or cls._map_columns(raw_headers)

        return cls._build_parsed_portfolio(
            filename=filename,
            file_type=file_type,
            raw_headers=raw_headers,
            col_map=col_map,
            data_rows=data_rows,
            metadata=metadata
        )

    @classmethod
    def _parse_pdf(
        cls,
        content: bytes,
        filename: str,
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedPortfolio:
        """Extracts text and table rows from PDF holding statements."""
        from pypdf import PdfReader

        bio = io.BytesIO(content)
        try:
            reader = PdfReader(bio)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    res = ParsedPortfolio(
                        filename=filename,
                        file_type="pdf",
                        statement_date="Not available in uploaded file",
                        client_name="Not available in uploaded file",
                        client_id="Not available in uploaded file",
                        reported_invested=None,
                        reported_current=None,
                        reported_pnl=None,
                    )
                    res.errors.append("PDF is password-protected. Please provide an unlocked statement.")
                    return res
        except Exception as e:
            res = ParsedPortfolio(
                filename=filename,
                file_type="pdf",
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append(f"Corrupted or invalid PDF file: {e}")
            return res

        full_text = ""
        for page in reader.pages:
            t = page.extract_text() or ""
            full_text += t + "\n"

        lines = [l.strip() for l in full_text.splitlines() if l.strip()]

        # Metadata search in top lines
        metadata = {}
        for line in lines[:25]:
            date_m = re.search(r"(?:date|statement date|as on)\s*[:\-]?\s*([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4})", line, re.I)
            if date_m and "Date" not in metadata:
                metadata["Date"] = date_m.group(1)
            client_m = re.search(r"(?:client id|account id|ucc)\s*[:\-]?\s*([A-Za-z0-9]+)", line, re.I)
            if client_m and "Client ID" not in metadata:
                metadata["Client ID"] = client_m.group(1)

        # Look for table lines: detect lines that contain ISIN or symbol + numbers
        table_rows = []
        raw_headers = ["Symbol", "Quantity", "Buy Price", "Current Price", "Current Value", "ISIN"]

        for line in lines:
            # Pattern: Ticker/Name followed by numbers and optionally an ISIN
            isin_match = re.search(r"(INE[A-Z0-9]{9})", line)
            isin = isin_match.group(1) if isin_match else ""

            # Check if line has numbers resembling prices and quantities
            tokens = re.split(r"\s{2,}|\t|,", line)
            if len(tokens) >= 4:
                # Potential table row
                num_count = sum(1 for tok in tokens if re.search(r"^[0-9,]+(\.[0-9]+)?$", tok.strip()))
                if num_count >= 2:
                    table_rows.append(tokens)

        if not table_rows:
            # Fallback: try whitespace split on lines that contain ISIN or stock patterns
            for line in lines:
                parts = line.split()
                if len(parts) >= 4 and any(re.search(r"^[0-9,]+(\.[0-9]+)?$", p) for p in parts):
                    table_rows.append(parts)

        if not table_rows:
            res = ParsedPortfolio(
                filename=filename,
                file_type="pdf",
                statement_date=metadata.get("Date", "Not available in uploaded file"),
                client_name="Not available in uploaded file",
                client_id=metadata.get("Client ID", "Not available in uploaded file"),
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append("Could not extract tabular stock holdings from the PDF statement. Please upload CSV or Excel.")
            return res

        # Map by position
        col_map = custom_mapping or {
            "symbol": "0",
            "quantity": "1",
            "buy_price": "2",
            "current_price": "3",
            "current_value": "4" if len(table_rows[0]) > 4 else "3",
            "isin": str(len(table_rows[0]) - 1) if any("INE" in t for t in table_rows[0]) else ""
        }

        # Clean table rows to index dicts
        mapped_rows = []
        for r in table_rows:
            mapped_rows.append(r)

        return cls._build_parsed_portfolio(
            filename=filename,
            file_type="pdf",
            raw_headers=[str(i) for i in range(max(len(r) for r in table_rows))],
            col_map=col_map,
            data_rows=mapped_rows,
            metadata=metadata
        )

    @classmethod
    def _parse_docx(
        cls,
        content: bytes,
        filename: str,
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedPortfolio:
        """Extracts tables and metadata from Word .docx statements."""
        import docx

        bio = io.BytesIO(content)
        try:
            doc = docx.Document(bio)
        except Exception as e:
            res = ParsedPortfolio(
                filename=filename,
                file_type="docx",
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append(f"Failed to open DOCX document: {e}")
            return res

        # Extract metadata from paragraphs
        metadata = {}
        for p in doc.paragraphs[:15]:
            txt = p.text.strip()
            if ":" in txt:
                parts = txt.split(":", 1)
                metadata[parts[0].strip()] = parts[1].strip()

        # Find largest table
        if not doc.tables:
            res = ParsedPortfolio(
                filename=filename,
                file_type="docx",
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append("No tables found in DOCX file.")
            return res

        target_table = max(doc.tables, key=lambda t: len(t.rows))
        all_rows = []
        for row in target_table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                all_rows.append(cells)

        if len(all_rows) < 2:
            res = ParsedPortfolio(
                filename=filename,
                file_type="docx",
                statement_date="Not available in uploaded file",
                client_name="Not available in uploaded file",
                client_id="Not available in uploaded file",
                reported_invested=None,
                reported_current=None,
                reported_pnl=None,
            )
            res.errors.append("Table in DOCX does not contain sufficient rows.")
            return res

        raw_headers = all_rows[0]
        data_rows = all_rows[1:]
        col_map = custom_mapping or cls._map_columns(raw_headers)

        return cls._build_parsed_portfolio(
            filename=filename,
            file_type="docx",
            raw_headers=raw_headers,
            col_map=col_map,
            data_rows=data_rows,
            metadata=metadata
        )

    @classmethod
    def _is_table_header(cls, row: List[str]) -> bool:
        """Determines if a row looks like a broker holdings table header."""
        if not row or len(row) < 3:
            return False
        clean_cells = [c.strip().lower() for c in row if c.strip()]
        matched_categories = 0

        for cat, patterns in cls.COLUMN_PATTERNS.items():
            if any(any(re.search(pat, cell) for pat in patterns) for cell in clean_cells):
                matched_categories += 1

        # Must match at least symbol and (quantity or price or invested/current value)
        return matched_categories >= 3

    @classmethod
    def _map_columns(cls, headers: List[str]) -> Dict[str, str]:
        """Automatically maps detected table headers to standard fields."""
        mapping = {}
        for idx, h in enumerate(headers):
            h_clean = h.strip().lower()
            if not h_clean:
                continue

            for field_name, patterns in cls.COLUMN_PATTERNS.items():
                if field_name in mapping:
                    continue
                for pat in patterns:
                    if re.search(pat, h_clean):
                        mapping[field_name] = str(idx)
                        break

        # If name not mapped but symbol is, symbol acts as name
        if "symbol" in mapping and "name" not in mapping:
            mapping["name"] = mapping["symbol"]

        return mapping

    @classmethod
    def _build_parsed_portfolio(
        cls,
        filename: str,
        file_type: str,
        raw_headers: List[str],
        col_map: Dict[str, str],
        data_rows: List[List[str]],
        metadata: Dict[str, Any]
    ) -> ParsedPortfolio:
        """Constructs standardized ParsedPortfolio and extracts holdings."""
        # Normalize statement date
        stmt_date = metadata.get("Date") or metadata.get("Statement Date") or metadata.get("As On") or "Not available in uploaded file"
        if stmt_date != "Not available in uploaded file":
            stmt_date = str(stmt_date).strip()

        client_name = metadata.get("Client Name") or metadata.get("Name") or "Not available in uploaded file"
        client_id = metadata.get("Client ID") or metadata.get("Account ID") or metadata.get("Client Id") or "Not available in uploaded file"

        reported_invested = cls.clean_number(metadata.get("Total Invested") or metadata.get("Total Investment"))
        reported_current = cls.clean_number(metadata.get("Total Current") or metadata.get("Current Value"))
        reported_pnl = cls.clean_number(metadata.get("Profit & loss") or metadata.get("Total P&L"))

        portfolio = ParsedPortfolio(
            filename=filename,
            file_type=file_type,
            statement_date=stmt_date,
            client_name=client_name,
            client_id=client_id,
            reported_invested=reported_invested if reported_invested > 0 else None,
            reported_current=reported_current if reported_current > 0 else None,
            reported_pnl=reported_pnl if reported_pnl != 0 else None,
            raw_headers=raw_headers,
            detected_column_map=col_map,
            metadata=metadata
        )

        # Helper to get cell value by mapped field name
        def get_cell(row: List[str], f_name: str) -> str:
            if f_name not in col_map:
                return ""
            try:
                col_idx = int(col_map[f_name])
                if 0 <= col_idx < len(row):
                    return row[col_idx].strip()
            except (ValueError, TypeError):
                pass
            return ""

        holdings: List[ParsedHolding] = []
        for r_idx, row in enumerate(data_rows):
            if not row or not any(c.strip() for c in row):
                continue

            raw_sym = get_cell(row, "symbol")
            raw_name = get_cell(row, "name")

            if not raw_sym and not raw_name:
                continue

            # Ignore summary/footer rows
            check_str = (raw_sym or raw_name).lower()
            if any(kw in check_str for kw in ["total", "summary", "grand total", "subtotal", "disclaimer"]):
                continue

            identifier = raw_sym or raw_name
            exchange, clean_symbol, yahoo_sym = cls.parse_exchange_and_symbol(identifier)

            qty = cls.clean_number(get_cell(row, "quantity"))
            buy_price = cls.clean_number(get_cell(row, "buy_price"))
            curr_price = cls.clean_number(get_cell(row, "current_price"))
            invested = cls.clean_number(get_cell(row, "invested_amount"))
            curr_val = cls.clean_number(get_cell(row, "current_value"))
            pnl_amt = cls.clean_number(get_cell(row, "pnl_amount"))
            pnl_pct = cls.clean_number(get_cell(row, "pnl_pct"))
            isin = get_cell(row, "isin") or "Not available in uploaded file"
            sector = get_cell(row, "sector") or "Not available in uploaded file"

            # Derive missing mathematical quantities
            notes = []
            if qty > 0 and buy_price > 0 and invested == 0:
                invested = round(qty * buy_price, 2)
            elif qty > 0 and invested > 0 and buy_price == 0:
                buy_price = round(invested / qty, 2)

            if qty > 0 and curr_price > 0 and curr_val == 0:
                curr_val = round(qty * curr_price, 2)
            elif qty > 0 and curr_val > 0 and curr_price == 0:
                curr_price = round(curr_val / qty, 2)

            if curr_val > 0 and invested > 0:
                calculated_pnl = round(curr_val - invested, 2)
                calculated_pct = round((calculated_pnl / invested) * 100.0, 2)
                if pnl_amt == 0:
                    pnl_amt = calculated_pnl
                if pnl_pct == 0:
                    pnl_pct = calculated_pct

            # Validation checks
            if qty <= 0:
                notes.append("Quantity was zero or could not be verified.")
            if buy_price <= 0:
                notes.append("Buy price missing or zero.")
            if curr_price <= 0:
                notes.append("Current price missing or zero.")

            # Formulate friendly stock name
            stock_name = raw_name if raw_name and raw_name != raw_sym else clean_symbol

            holding = ParsedHolding(
                stock_name=stock_name,
                symbol=yahoo_sym,
                clean_symbol=clean_symbol,
                exchange=exchange,
                isin=isin,
                quantity=qty,
                buy_price=buy_price,
                current_price=curr_price,
                invested_amount=invested,
                current_value=curr_val,
                pnl_amount=pnl_amt,
                pnl_pct=pnl_pct,
                sector=sector,
                statement_date=stmt_date,
                raw_symbol=identifier,
                validation_notes=notes
            )
            holdings.append(holding)

        portfolio.holdings = holdings
        if not holdings:
            portfolio.warnings.append("No valid stock holding records could be extracted from the uploaded statement.")

        logger.info(f"Extracted {len(holdings)} holdings from {filename}. Total Value: INR {portfolio.total_current_calculated:,.2f}")
        return portfolio
