"""Hallen-Lookup (SPEC.md Abschnitt 8)."""

from __future__ import annotations

from .config import Hall
from .textnorm import normalize


def find_hall(halls: list[Hall], text: str) -> Hall | None:
    """Sucht eine Halle, deren normalisierter Suchbegriff als Teilstring im
    normalisierten `text` vorkommt (nicht nur Gleichheit) -- z.B. muss
    "Training - Flehenberg Gruppe B" noch auf die Halle Flehenberg treffen.
    Bei mehreren Treffern gewinnt der längste Suchbegriff.
    """
    if not text:
        return None
    normalized_text = normalize(text)
    if not normalized_text:
        return None

    best: Hall | None = None
    best_len = -1
    for hall in halls:
        for term in hall.search_terms:
            normalized_term = normalize(term)
            if normalized_term and normalized_term in normalized_text:
                if len(normalized_term) > best_len:
                    best = hall
                    best_len = len(normalized_term)
    return best


def hall_address(hall: Hall) -> str:
    """Vollständiger LOCATION-String inkl. ', Deutschland' (SPEC.md Abschnitt 8)."""
    return f"{hall.name}, {hall.address}, Deutschland"
