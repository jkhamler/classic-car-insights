"""Match raw listing make/model strings to canonical vehicles."""
from sqlalchemy.orm import Session
from app.db.models.vehicle import Vehicle

ALIASES: dict[str, tuple[str, str, str | None]] = {
    # (normalized_key) -> (make, model, generation)
    # Porsche
    "porsche 996": ("Porsche", "911", "996"),
    "porsche 997": ("Porsche", "911", "997"),
    "porsche 911 996": ("Porsche", "911", "996"),
    "porsche 911 997": ("Porsche", "911", "997"),
    "porsche boxster 986": ("Porsche", "Boxster", "986"),
    "porsche cayman 987": ("Porsche", "Cayman", "987"),
    "porsche 944": ("Porsche", "944", "944"),
    # BMW
    "bmw m3 e36": ("BMW", "M3", "E36"),
    "bmw m3 e46": ("BMW", "M3", "E46"),
    "bmw m3 e90": ("BMW", "M3", "E90/E92"),
    "bmw m3 e92": ("BMW", "M3", "E90/E92"),
    "bmw m5 e39": ("BMW", "M5", "E39"),
    "bmw m5 e60": ("BMW", "M5", "E60"),
    # Nissan
    "nissan skyline r32": ("Nissan", "Skyline GT-R", "R32"),
    "nissan skyline r33": ("Nissan", "Skyline GT-R", "R33"),
    "nissan skyline r34": ("Nissan", "Skyline GT-R", "R34"),
    "nissan gt-r r32": ("Nissan", "Skyline GT-R", "R32"),
    "nissan gt-r r33": ("Nissan", "Skyline GT-R", "R33"),
    "nissan gt-r r34": ("Nissan", "Skyline GT-R", "R34"),
    "nissan gtr r34": ("Nissan", "Skyline GT-R", "R34"),
    "nissan 350z": ("Nissan", "350Z", "Z33"),
    # Toyota
    "toyota supra": ("Toyota", "Supra", "A80"),
    "toyota supra a80": ("Toyota", "Supra", "A80"),
    "toyota mr2 sw20": ("Toyota", "MR2", "SW20"),
    "toyota mr2": ("Toyota", "MR2", "SW20"),
    # Honda
    "honda nsx": ("Honda", "NSX", "NA1/NA2"),
    "honda s2000": ("Honda", "S2000", "AP1/AP2"),
    "honda integra type r": ("Honda", "Integra Type R", "DC2"),
    "honda integra": ("Honda", "Integra Type R", "DC2"),
    # Mazda
    "mazda rx-7": ("Mazda", "RX-7", "FD"),
    "mazda rx7": ("Mazda", "RX-7", "FD"),
    "mazda mx-5 na": ("Mazda", "MX-5", "NA"),
    "mazda mx-5 nb": ("Mazda", "MX-5", "NB"),
    "mazda miata na": ("Mazda", "MX-5", "NA"),
    "mazda miata nb": ("Mazda", "MX-5", "NB"),
    "mazda mx5": ("Mazda", "MX-5", "NA"),
    "mazda miata": ("Mazda", "MX-5", "NA"),
    # Mitsubishi
    "mitsubishi evo vi": ("Mitsubishi", "Lancer Evolution", "VI"),
    "mitsubishi evo 6": ("Mitsubishi", "Lancer Evolution", "VI"),
    "mitsubishi lancer evolution vi": ("Mitsubishi", "Lancer Evolution", "VI"),
    "mitsubishi evo": ("Mitsubishi", "Lancer Evolution", "VII-IX"),
    "mitsubishi lancer evolution": ("Mitsubishi", "Lancer Evolution", "VII-IX"),
    # Subaru
    "subaru impreza wrx sti": ("Subaru", "Impreza WRX STI", "GD"),
    "subaru impreza sti": ("Subaru", "Impreza WRX STI", "GD"),
    "subaru wrx sti": ("Subaru", "Impreza WRX STI", "GD"),
    "subaru impreza": ("Subaru", "Impreza WRX STI", "GD"),
    # Mercedes
    "mercedes c63": ("Mercedes-Benz", "C63 AMG", "W204"),
    "mercedes c63 amg": ("Mercedes-Benz", "C63 AMG", "W204"),
    "mercedes sl r129": ("Mercedes-Benz", "SL", "R129"),
    "mercedes sl": ("Mercedes-Benz", "SL", "R129"),
    # Lotus
    "lotus elise s1": ("Lotus", "Elise", "S1"),
    "lotus elise s2": ("Lotus", "Elise", "S2"),
    "lotus elise": ("Lotus", "Elise", "S2"),
    "lotus exige": ("Lotus", "Exige", "S2"),
    # Alfa Romeo
    "alfa romeo gtv": ("Alfa Romeo", "GTV", "916"),
    "alfa gtv": ("Alfa Romeo", "GTV", "916"),
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
