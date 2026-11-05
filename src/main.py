"""Main CLI entry point for the AI Stock Research Agent."""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*inplace keyword.*")

# pandas 3.1 Pandas4Warning bypasses filterwarnings — intercept at showwarning level
_original_showwarning = warnings.showwarning
def _filtered_showwarning(message, category, filename, lineno, file=None, line=None):
    if category.__name__ == "Pandas4Warning":
        return
    _original_showwarning(message, category, filename, lineno, file, line)
warnings.showwarning = _filtered_showwarning

import typer
from typing import Optional, List
from datetime import date, datetime, timedelta
from pathlib import Path

from src.utils.logger import setup_logger, logger
from src.config import get_config
from src.storage.database import DatabaseManager, StockRepository
from src.agents.universe_agent import UniverseAgent
from src.agents.fundamentals_agent import FundamentalsAgent
from src.agents.technical_agent import TechnicalAgent
from src.agents.news_agent import NewsAgent
from src.agents.filings_agent import FilingsAgent
from src.agents.sector_agent import SectorAgent
from src.agents.risk_agent import RiskAgent
from src.agents.ranking_agent import RankingAgent
from src.data.market_data import get_market_data_provider
from src.data.fundamentals import enrich_fundamental_data
from src.analysis.backtest import PointInTimeBacktester
from src.utils.report_generator import MarkdownReportGenerator, CSVExporter, PDFReportGenerator
from src.utils.helpers import format_inr

app = typer.Typer(help="AI Stock Market Research & Ranking Agent for NSE and BSE")

# Initialize config and logger
config = get_config()
setup_logger(log_file=config.system.log_file, level=config.system.log_level)

# Initialize shared components
db_manager = DatabaseManager(config.system.db_path)
db_manager.init_db()
repo = StockRepository(db_manager)
md_provider = get_market_data_provider()

# Initialize agents
universe_agent = UniverseAgent(repo)
fundamentals_agent = FundamentalsAgent(repo)
technical_agent = TechnicalAgent(repo)
news_agent = NewsAgent(repo)
filings_agent = FilingsAgent(repo)
sector_agent = SectorAgent(repo)
risk_agent = RiskAgent(repo)
ranking_agent = RankingAgent(repo)


@app.command()
def build_universe(
    index: str = typer.Option("nifty500", help="Index to use: nifty500, bse500, or custom"),
    custom_symbols: Optional[str] = typer.Option(None, help="Comma-separated custom symbols"),
    force_refresh: bool = typer.Option(False, help="Force refresh of universe data")
):
    """Build the investable stock universe."""
    symbols = None
    if custom_symbols:
        symbols = [s.strip() for s in custom_symbols.split(",")]
        
    result = universe_agent.build_universe(index=index, custom_symbols=symbols, force_refresh=force_refresh)
    
    typer.echo(f"Universe built from {result['source']}")
    typer.echo(f"Input symbols: {result['total_input']}")
    typer.echo(f"Passed screening: {result['passed_screening']}")
    typer.echo(f"Final universe: {result['final_universe']} stocks")
    
    if result['excluded']:
        typer.echo(f"Excluded: {len(result['excluded'])} symbols")


@app.command()
def update_data(
    symbols: str = typer.Option(..., help="Comma-separated symbols to update"),
    period: str = typer.Option("2y", help="Price history period")
):
    """Update price history and fundamental data for symbols."""
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    for sym in symbol_list:
        typer.echo(f"Updating {sym}...")
        
        # Price history
        df = md_provider.get_price_history(sym, period=period)
        if df is not None and not df.empty:
            count = repo.bulk_upsert_prices(sym, df)
            typer.echo(f"  Price history: {count} records")
            
        # Company info
        info = md_provider.get_company_info(sym)
        if info:
            info.pop("symbol", None)  # Avoid conflict with positional arg
            repo.upsert_stock(sym, **info)
            typer.echo(f"  Company info updated")
            
        # Fundamentals
        fund_data = md_provider.get_fundamental_data(sym)
        if fund_data:
            enriched = enrich_fundamental_data(fund_data, md_provider.get_current_price(sym))
            repo.upsert_fundamentals(sym, enriched)
            typer.echo(f"  Fundamentals updated")


@app.command()
def analyze(
    index: str = typer.Option("nifty500", help="Universe index"),
    top: int = typer.Option(20, help="Number of top stocks to analyze"),
    custom_symbols: Optional[str] = typer.Option(None, help="Comma-separated custom symbols"),
    sector: Optional[str] = typer.Option(None, help="Filter by sector"),
    min_market_cap: Optional[float] = typer.Option(None, help="Minimum market cap in Crores"),
    output_dir: str = typer.Option("data/reports", help="Output directory for reports")
):
    """Run full analysis pipeline and generate ranked watchlist."""
    
    # 1. Build/Filter Universe
    if custom_symbols:
        symbols = [s.strip() for s in custom_symbols.split(",")]
    else:
        symbols = universe_agent.get_universe_symbols(index)
        
    if sector or min_market_cap:
        symbols = universe_agent.filter_universe(
            symbols, 
            sector=sector, 
            min_market_cap_cr=min_market_cap
        )
        
    if not custom_symbols and top and top > 0 and len(symbols) > top:
        symbols = symbols[:top]
        
    typer.echo(f"Analyzing {len(symbols)} symbols...")
    
    # 2. Run all agents for each symbol
    agent_outputs = {}
    for i, sym in enumerate(symbols):
        typer.echo(f"  [{i+1}/{len(symbols)}] {sym}...")
        
        outputs = {}
        
        # Fundamentals
        outputs["fundamentals"] = fundamentals_agent.analyze(sym)
        
        # Technical
        outputs["technical"] = technical_agent.analyze(sym)
        
        # News
        outputs["news"] = news_agent.analyze(sym)
        
        # Filings
        outputs["filings"] = filings_agent.analyze(sym)
        
        # Sector
        outputs["sector"] = sector_agent.analyze(sym)
        
        # Risk (needs scores from fundamentals)
        fund_out = outputs["fundamentals"]
        ratios = fund_out.get("ratios", {})
        growth_metrics = fund_out.get("growth_metrics", {})
        red_flags = fund_out.get("red_flags", [])
        governance_flags = outputs["filings"].get("structured_flags", {}).get("governance_red_flags", [])
        news_sentiment = outputs["news"].get("aggregate_metrics", {}).get("avg_sentiment", 0)
        
        # Quick quality/growth scores for risk agent
        from src.analysis.scoring import ScoringEngine
        scoring = ScoringEngine()
        quality = scoring.score_quality(ratios, red_flags)
        growth = scoring.score_growth(growth_metrics, [fund_out.get("fundamental_data", {})])
        
        outputs["risk"] = risk_agent.analyze(
            sym, quality, growth, 50, 50, ratios, red_flags, governance_flags, news_sentiment
        )
        
        agent_outputs[sym] = outputs
        
    # 3. Rank
    typer.echo("Ranking stocks...")
    ranked = ranking_agent.rank_universe(symbols, agent_outputs, top_n=top)
    
    # 4. Generate Reports
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Markdown Report
    md_gen = MarkdownReportGenerator()
    disclaimer = config.compliance.disclaimer
    
    md_content = md_gen.generate_header(f"AI Stock Research Watchlist - {timestamp}", disclaimer)
    md_content += md_gen.generate_executive_summary(
        len(ranked), 
        date.today().isoformat(),
        f"Analyzed {len(symbols)} stocks from {index}. Top {len(ranked)} ranked by composite score."
    )
    md_content += md_gen.generate_ranked_table(ranked)
    
    for stock in ranked:
        md_content += md_gen.generate_detailed_stock_report(stock, config.model_dump())
        
    md_content += f"\n\n---\n{disclaimer}\n"
    
    md_file = output_path / f"watchlist_{timestamp}.md"
    md_gen.save_report(md_content, md_file)
    typer.echo(f"Markdown report saved: {md_file}")
    
    # CSV Export
    csv_file = output_path / f"watchlist_{timestamp}.csv"
    CSVExporter.export(ranked, csv_file)
    typer.echo(f"CSV export saved: {csv_file}")
    
    # PDF Report
    try:
        pdf_gen = PDFReportGenerator()
        pdf_gen.add_title_page(f"AI Stock Research Watchlist", date.today().isoformat(), disclaimer)
        
        # Summary table
        headers = ["Rank", "Symbol", "Name", "Sector", "MCap", "Score", "Quality", "Growth", "Val", "Mom", "Cat", "Risk"]
        col_widths = [12, 18, 35, 22, 18, 12, 12, 12, 12, 12, 12, 12]
        data = []
        for s in ranked:
            data.append([
                s["rank"], s["symbol"], s["name"][:20], s["sector"][:15],
                s["market_cap_str"], f'{s["composite_score"]:.1f}',
                f'{s["quality_score"]:.1f}', f'{s["growth_score"]:.1f}',
                f'{s["valuation_score"]:.1f}', f'{s["momentum_score"]:.1f}',
                f'{s["catalyst_score"]:.1f}', f'{s["risk_score"]:.1f}'
            ])
        pdf_gen.add_table(headers, data, col_widths)
        
        pdf_file = output_path / f"watchlist_{timestamp}.pdf"
        pdf_gen.save(pdf_file)
        typer.echo(f"PDF report saved: {pdf_file}")
    except Exception as e:
        typer.echo(f"PDF generation failed: {e}")
        
    typer.echo(f"\nAnalysis complete! Top {len(ranked)} stocks ranked.")


@app.command()
def backtest(
    start: str = typer.Option(..., help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., help="End date (YYYY-MM-DD)"),
    index: str = typer.Option("nifty500", help="Universe index"),
    top_n: int = typer.Option(10, help="Number of stocks in portfolio"),
    frequency: str = typer.Option("M", help="Rebalance frequency: M or Q"),
    capital: float = typer.Option(1000000, help="Initial capital in INR")
):
    """Run point-in-time backtest of the ranking strategy."""
    
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    
    # Get universe symbols
    symbols = universe_agent.get_universe_symbols(index)
    typer.echo(f"Backtesting {len(symbols)} symbols from {start_date} to {end_date}")
    
    # Run backtest
    backtester = PointInTimeBacktester(repo)
    result = backtester.run_backtest(
        universe_symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        rebalance_freq=frequency,
        top_n=top_n,
        initial_capital=capital
    )
    
    # Save results
    report_path = backtester.save_results(result)
    
    # Display results
    typer.echo(f"\n=== BACKTEST RESULTS ===")
    typer.echo(f"Period: {start_date} to {end_date}")
    typer.echo(f"Initial Capital: {format_inr(capital)}")
    typer.echo(f"Final Capital: {format_inr(result.final_capital)}")
    typer.echo(f"CAGR: {result.cagr:.2%}")
    typer.echo(f"Volatility: {result.volatility:.2%}")
    typer.echo(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    typer.echo(f"Max Drawdown: {result.max_drawdown:.2%}")
    typer.echo(f"Win Rate: {result.win_rate:.2%}")
    typer.echo(f"Benchmark CAGR: {result.benchmark_cagr:.2%}")
    typer.echo(f"Alpha: {result.alpha:.2%}")
    typer.echo(f"Beta: {result.beta:.2f}")
    typer.echo(f"Report saved: {report_path}")
    
    # Compliance disclaimer
    typer.echo(f"\n{config.compliance.disclaimer}")


@app.command()
def dashboard(port: int = 8000):
    """Launch Django institutional web platform."""
    import subprocess
    import sys
    typer.echo(f"Starting Django Web Platform on http://127.0.0.1:{port}/ ...")
    subprocess.run([sys.executable, "manage.py", "runserver", str(port)])


# Register underscore aliases so both hyphenated and underscored CLI syntax work identically
app.command(name="build_universe", hidden=True)(build_universe)
app.command(name="update_data", hidden=True)(update_data)

if __name__ == "__main__":
    app()