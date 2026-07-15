"""Match raw listing make/model strings to canonical vehicles."""
from sqlalchemy.orm import Session
from app.db.models.vehicle import Vehicle

ALIASES: dict[str, tuple[str, str, str | None]] = {
    # (normalized_key) -> (make, model, generation)
    # Porsche 911 — extract_make_model() labels these "911 996"/"911 997" (with
    # "Turbo" suffix where relevant), which doesn't substring-match the
    # model="911"/generation="996|997" schema, so they need explicit aliases.
    "porsche 911 996 turbo": ("Porsche", "911", "996"),
    "porsche 911 996": ("Porsche", "911", "996"),
    "porsche 996 turbo": ("Porsche", "911", "996"),
    "porsche 996": ("Porsche", "911", "996"),
    "porsche 911 997 turbo": ("Porsche", "911", "997"),
    "porsche 911 997": ("Porsche", "911", "997"),
    "porsche 997 turbo": ("Porsche", "911", "997"),
    "porsche 997": ("Porsche", "911", "997"),
}


def _normalize(text: str) -> str:
    return text.lower().strip().replace("-", " ").replace("_", " ")


def match_vehicle(db: Session, make: str | None, model: str | None, title: str | None = None, year: int | None = None) -> Vehicle | None:
    search_parts = []
    if make:
        search_parts.append(_normalize(make))
    if model:
        search_parts.append(_normalize(model))
    search_key = " ".join(search_parts)

    # Try alias dictionary first
    for alias_key, (v_make, v_model, v_gen) in ALIASES.items():
        if alias_key in search_key or (title and alias_key in _normalize(title)):
            vehicle = (
                db.query(Vehicle)
                .filter(Vehicle.make == v_make, Vehicle.model == v_model, Vehicle.generation == v_gen)
                .first()
            )
            if vehicle:
                return vehicle

    if not make:
        return None

    # Try exact match with year range
    candidates = (
        db.query(Vehicle)
        .filter(Vehicle.make.ilike(f"%{make.strip()}%"))
    )
    if model:
        candidates = candidates.filter(Vehicle.model.ilike(f"%{model.strip()}%"))
    candidates = candidates.all()

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # Multiple candidates — use year to pick the best one
    if year:
        for v in candidates:
            start = v.year_start or 0
            end = v.year_end or 9999
            if start <= year <= end:
                return v
        # No exact year match — return closest by year
        candidates.sort(key=lambda v: min(abs((v.year_start or 0) - year), abs((v.year_end or 9999) - year)))
        return candidates[0]

    # No year — return first candidate
    return candidates[0]
