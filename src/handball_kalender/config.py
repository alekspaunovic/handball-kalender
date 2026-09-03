"""Laden von config.yaml und halls.yaml (SPEC.md Abschnitt 4, 8, 11)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class TeamConfig:
    key: str
    anzeigename: str
    handballnet_name: str
    handballnet_team_id: int
    spielerplus_env: str
    treffpunkt_spiel_minuten: int
    treffpunkt_training_minuten: int | None
    spieldauer_minuten: int


@dataclass(frozen=True)
class FeedConfig:
    key: str
    team: str
    type: str  # "training" oder "spiele"


@dataclass(frozen=True)
class Hall:
    key: str
    name: str
    search_terms: list[str]
    address: str
    geo: tuple[float, float] | None


@dataclass(frozen=True)
class Config:
    timezone: str
    feed_ttl: str
    uid_prefix: str
    output_dir: str
    archive_dir: str
    teams: dict[str, TeamConfig]
    feeds: dict[str, FeedConfig]
    opponent_overrides: dict[str, str]
    halls: list[Hall] = field(default_factory=list)

    def spielerplus_url(self, team_key: str) -> str | None:
        return os.environ.get(self.teams[team_key].spielerplus_env)


def load_halls(path: str | Path) -> list[Hall]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    halls = []
    for key, entry in raw.items():
        geo = entry.get("geo")
        halls.append(
            Hall(
                key=key,
                name=entry["name"],
                search_terms=list(entry["search_terms"]),
                address=entry["address"],
                geo=tuple(geo) if geo else None,
            )
        )
    return halls


def load_config(config_path: str | Path, halls_path: str | Path) -> Config:
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}

    teams = {
        key: TeamConfig(key=key, **team_raw) for key, team_raw in raw["teams"].items()
    }
    feeds = {
        key: FeedConfig(key=key, **feed_raw) for key, feed_raw in raw["feeds"].items()
    }

    return Config(
        timezone=raw["timezone"],
        feed_ttl=raw["feed_ttl"],
        uid_prefix=raw["uid_prefix"],
        output_dir=raw["output_dir"],
        archive_dir=raw["archive_dir"],
        teams=teams,
        feeds=feeds,
        opponent_overrides=dict(raw.get("opponent_overrides") or {}),
        halls=load_halls(halls_path),
    )
