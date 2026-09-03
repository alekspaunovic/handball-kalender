"""Transformation von SpielerPlus-Terminen (SPEC.md Abschnitt 2 + 5)."""

from __future__ import annotations

import logging
import re
from datetime import timedelta

from .config import Hall, TeamConfig
from .halls import find_hall, hall_address
from .ics_io import extract_geo, extract_location
from .models import Event

logger = logging.getLogger(__name__)

_TRAINING_TITLE_RE = re.compile(r"^Training\s*-\s*(.+)$")


def classify_uid(uid: str) -> str:
    """Ordnet eine SpielerPlus-UID einer Kategorie zu (SPEC.md Abschnitt 2).

    "training" und "event" werden übernommen, "spiel" wird verworfen (die
    Spieldaten kommen aus handball.net), unbekannte Präfixe werden wie
    "event" behandelt und geloggt, damit nichts stillschweigend verloren
    geht.
    """
    prefix = uid.split(".", 1)[0]
    if prefix in ("training", "event"):
        return prefix
    if prefix == "spiel":
        return "spiel"
    logger.warning("Unbekanntes SpielerPlus-UID-Präfix %r, wird wie 'event' behandelt", uid)
    return "event"


def _source_id(uid: str) -> str:
    return uid.split(".", 1)[1] if "." in uid else uid


def build_title(anzeigename: str, raw_summary: str) -> tuple[str, str | None]:
    """Titel gemäß SPEC.md Abschnitt 5 sowie den erkannten Ortszusatz, falls
    vorhanden."""
    if raw_summary == "Training":
        return f"Training {anzeigename}", None

    match = _TRAINING_TITLE_RE.match(raw_summary)
    if match:
        ortszusatz = match.group(1).strip()
        return f"Training {anzeigename} - {ortszusatz}", ortszusatz

    return f"{anzeigename}: {raw_summary}", None


def resolve_location(
    halls: list[Hall],
    location: str | None,
    geo: tuple[float, float] | None,
    ortszusatz: str | None,
) -> tuple[str, tuple[float, float] | None]:
    """Ort-Regel gemäß der korrigierten SPEC.md Abschnitt 5.

    1. Quelle liefert LOCATION: verwenden (inkl. GEO), außer die Adresse
       entspricht einer bekannten Halle -- dann den Hallentabellen-Eintrag
       nehmen (einheitliche Schreibweise).
    2. Keine LOCATION, aber bekannter Ortszusatz: Halle aus der Tabelle.
    3. Keine LOCATION und kein Ortszusatz: Standardhalle Fliethe.
    4. Keine LOCATION und unbekannter Ortszusatz: Ortszusatz als reinen Text,
       Warnung loggen.
    """
    if location:
        hall = find_hall(halls, location)
        if hall:
            return hall_address(hall), hall.geo
        return location, geo

    if ortszusatz:
        hall = find_hall(halls, ortszusatz)
        if hall:
            return hall_address(hall), hall.geo
        logger.warning("Unbekannter Ortszusatz %r, wird als reiner Text übernommen", ortszusatz)
        return ortszusatz, None

    fliethe = next(h for h in halls if h.key == "fliethe")
    return hall_address(fliethe), fliethe.geo


def build_notiz(kind: str, team: TeamConfig, dtstart) -> str:
    if kind == "training" and team.treffpunkt_training_minuten is not None:
        treffpunkt = dtstart - timedelta(minutes=team.treffpunkt_training_minuten)
        return f"Treffpunkt: {treffpunkt.strftime('%H:%M')}"
    return ""


def transform(
    vevent,
    team: TeamConfig,
    halls: list[Hall],
    uid_prefix: str,
) -> Event | None:
    """Wandelt ein SpielerPlus-VEVENT in ein Event um, oder None, wenn es
    verworfen wird (Spiel-UID)."""
    source_uid = str(vevent["UID"])
    kind = classify_uid(source_uid)
    if kind == "spiel":
        return None

    raw_summary = str(vevent["SUMMARY"])
    title, ortszusatz = build_title(team.anzeigename, raw_summary)

    location = extract_location(vevent)
    geo = extract_geo(vevent)
    final_location, final_geo = resolve_location(halls, location, geo, ortszusatz)

    dtstart = vevent["DTSTART"].dt
    dtend = vevent["DTEND"].dt
    description = build_notiz(kind, team, dtstart)

    uid = f"{uid_prefix}-{team.key}-{kind}-{_source_id(source_uid)}"

    return Event(
        uid=uid,
        source_uid=source_uid,
        summary=title,
        dtstart=dtstart,
        dtend=dtend,
        all_day=False,
        location=final_location,
        geo=final_geo,
        description=description,
        url=str(vevent.get("URL", "")),
        cancelled=False,
    )
