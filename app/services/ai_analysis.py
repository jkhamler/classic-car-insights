"""Claude API integration for generating market insights."""
import logging
from pathlib import Path

import anthropic
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.crud.reports import create_report, get_report_for_listing, get_report_for_vehicle
from app.crud.benchmarks import get_latest_benchmark
from app.crud.listings import get_top_opportunities, count_active_for_vehicle
from app.db.models.listing import Listing
from app.db.models.vehicle import Vehicle
from app.db.models.source import Source
from app.db.models.price_benchmark import PriceBenchmark

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text()


def _get_client() -> anthropic.Anthropic:
    settings = Settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def generate_opportunity_explanation(db: Session, listing: Listing) -> str | None:
    cached = get_report_for_listing(db, listing.id)
    if cached:
        return cached.content

    benchmark = get_latest_benchmark(db, listing.vehicle_id) if listing.vehicle_id else None
    if not benchmark:
        return None

    source = db.query(Source).filter(Source.id == listing.source_id).first()
    score_details = listing.score_details or {}

    prompt_template = _load_prompt("opportunity_explanation")
    prompt = prompt_template.format(
        title=listing.title,
        make=listing.make or "Unknown",
        model=listing.model or "Unknown",
        year=listing.year or "Unknown",
        asking_price=listing.price_gbp or listing.asking_price or 0,
        mileage=f"{listing.mileage:,} {listing.mileage_unit}" if listing.mileage else "Unknown",
        location=listing.location or "Unknown",
        source_name=source.display_name if source else "Unknown",
        transmission=listing.transmission or "Unknown",
        benchmark_avg=benchmark.avg_price,
        benchmark_median=benchmark.median_price or benchmark.avg_price,
        benchmark_min=benchmark.min_price or 0,
        benchmark_max=benchmark.max_price or 0,
        sample_count=benchmark.sample_count,
        price_trend=benchmark.price_trend or 0,
        score=listing.undervaluation_score or 0,
        score_price=score_details.get("price_vs_benchmark", 0),
        score_mileage=score_details.get("mileage_adjustment", 0),
        score_trend=score_details.get("market_trend", 0),
        score_scarcity=score_details.get("scarcity", 0),
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text

        create_report(
            db,
            report_type="opportunity_analysis",
            title=f"Opportunity: {listing.title}",
            content=content,
            listing_id=listing.id,
            vehicle_id=listing.vehicle_id,
            metadata_json={"model": "claude-sonnet-4-6", "tokens": response.usage.output_tokens},
        )
        return content
    except Exception as e:
        logger.error(f"AI analysis failed for listing {listing.id}: {e}")
        return None


def generate_investment_thesis(db: Session, vehicle: Vehicle) -> str | None:
    cached = get_report_for_vehicle(db, vehicle.id)
    if cached:
        return cached.content

    benchmarks = (
        db.query(PriceBenchmark)
        .filter(PriceBenchmark.vehicle_id == vehicle.id)
        .order_by(PriceBenchmark.period)
        .all()
    )
    if not benchmarks:
        return None

    latest = benchmarks[-1]
    active_count = count_active_for_vehicle(db, vehicle.id)

    price_history_lines = []
    for b in benchmarks:
        trend_str = f" ({b.price_trend:+.1f}%)" if b.price_trend else ""
        price_history_lines.append(f"- {b.period}: £{b.avg_price:,.0f} ({b.sample_count} sales){trend_str}")
    price_history = "\n".join(price_history_lines) or "No price history available."

    prompt_template = _load_prompt("investment_thesis")
    prompt = prompt_template.format(
        make=vehicle.make,
        model=vehicle.model,
        generation=vehicle.generation or "",
        year_start=vehicle.year_start or "?",
        year_end=vehicle.year_end or "?",
        country=vehicle.country_of_origin or "Unknown",
        engine_type=vehicle.engine_type or "Unknown",
        price_history=price_history,
        current_avg=latest.avg_price,
        active_count=active_count,
        trend=latest.price_trend or 0,
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text

        create_report(
            db,
            report_type="investment_thesis",
            title=f"Investment Thesis: {vehicle.make} {vehicle.model} ({vehicle.generation})",
            content=content,
            vehicle_id=vehicle.id,
            metadata_json={"model": "claude-sonnet-4-6", "tokens": response.usage.output_tokens},
        )
        return content
    except Exception as e:
        logger.error(f"AI thesis failed for vehicle {vehicle.id}: {e}")
        return None


def generate_weekly_digest(db: Session) -> str | None:
    opportunities = get_top_opportunities(db, limit=10)
    if not opportunities:
        logger.info("No opportunities for weekly digest")
        return None

    opp_lines = []
    for l in opportunities:
        price = l.price_gbp or l.asking_price or 0
        score = l.undervaluation_score or 0
        opp_lines.append(f"- {l.title} — £{price:,.0f} (score: {score:.0f}/100) — {l.listing_url}")
    opp_text = "\n".join(opp_lines)

    from app.db.models.price_benchmark import PriceBenchmark
    from sqlalchemy import desc
    movers = (
        db.query(PriceBenchmark)
        .filter(PriceBenchmark.price_trend.isnot(None))
        .order_by(desc(PriceBenchmark.period))
        .limit(50)
        .all()
    )
    seen = {}
    for m in movers:
        if m.vehicle_id not in seen:
            seen[m.vehicle_id] = m
    top_movers = sorted(seen.values(), key=lambda b: abs(b.price_trend or 0), reverse=True)[:5]

    mover_lines = []
    for m in top_movers:
        v = db.query(Vehicle).filter(Vehicle.id == m.vehicle_id).first()
        if v:
            mover_lines.append(f"- {v.make} {v.model} ({v.generation}): {m.price_trend:+.1f}% — avg £{m.avg_price:,.0f}")
    movers_text = "\n".join(mover_lines) or "No significant movers this week."

    from sqlalchemy import func as sql_func
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_count = db.query(sql_func.count(Listing.id)).filter(Listing.scraped_at >= week_ago).scalar() or 0
    avg_score = db.query(sql_func.avg(Listing.undervaluation_score)).filter(
        Listing.undervaluation_score.isnot(None), Listing.scraped_at >= week_ago
    ).scalar() or 0

    prompt_template = _load_prompt("weekly_digest")
    prompt = prompt_template.format(
        opportunities=opp_text,
        movers=movers_text,
        new_listings_count=new_count,
        avg_score=f"{avg_score:.0f}",
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text

        create_report(
            db,
            report_type="weekly_digest",
            title="Weekly Market Digest",
            content=content,
            metadata_json={"model": "claude-sonnet-4-6", "tokens": response.usage.output_tokens},
        )
        return content
    except Exception as e:
        logger.error(f"Weekly digest generation failed: {e}")
        return None
