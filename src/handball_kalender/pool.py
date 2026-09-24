"""docs/pool.json erzeugen (SPEC-ADMIN.md Abschnitt 2).

Auswahlgrundlage fuer die Admin-Oberflaeche. Ein Browser darf die Spielplaene
von handball.net nicht direkt abrufen, deshalb legt der Workflow die Liste hier
ab.

Der Pool entsteht aus den Archiven, nicht aus den Quellen -- er enthaelt
deshalb auch ausgeblendete Termine. Sonst liesse sich ein Ausblenden nicht
wieder zuruecknehmen.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import Config
from .halls import hall_address

# Nur was die Oberflaeche braucht. geo, url und source_uid bleiben draussen,
# damit die Datei auf dem Handy klein bleibt.
def _pool_event(entry: dict, config: Config, feed_key: str) -> dict:
    feed = config.feeds[feed_key]
    team = config.teams[feed.team]
    return {
        "uid": entry["uid"],
        "team": team.anzeigename,
        "team_key": team.key,
        "own_team": team.own,
        "type": feed.type,
        "summary": entry["summary"],
        "dtstart": entry["dtstart"],
        "dtend": entry["dtend"],
        "all_day": entry["all_day"],
        "location": entry.get("location"),
        "cancelled": entry["cancelled"],
    }


def build(archives: dict[str, list[dict]], config: Config, now: datetime) -> dict:
    """`archives` bildet feed_key auf die gemergten Archiveintraege ab."""
    events = [
        _pool_event(entry, config, feed_key)
        for feed_key, entries in archives.items()
        for entry in entries
    ]
    events.sort(key=lambda event: (event["dtstart"], event["summary"]))
    # halls.yaml liegt im Repo-Wurzelverzeichnis und ist ueber GitHub Pages
    # nicht erreichbar. Die Ortsauswahl im Formular braucht die Liste aber --
    # also reist sie im Pool mit, aus demselben Grund, aus dem der Pool
    # ueberhaupt existiert.
    halls = [
        {"name": hall.name, "address": hall_address(hall)}
        for hall in sorted(config.halls, key=lambda hall: hall.name)
    ]
    return {"generated": now.isoformat(), "halls": halls, "events": events}


def save(path: str | Path, pool: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
