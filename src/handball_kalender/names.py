"""Gegnername-Normalisierung (SPEC.md Abschnitt 6) und Adressbereinigung für
handball.net-Rohdaten (SPEC.md Abschnitt 9)."""

from __future__ import annotations

import re

_ABBREVIATIONS = {
    "TV": "TV",
    "TB": "TB",
    "TSV": "TSV",
    "TUS": "TuS",
    "HV": "HV",
    "HC": "HC",
    "SV": "SV",
    "SG": "SG",
    "JSG": "JSG",
    "HSV": "HSV",
    "SSG": "SSG",
    "DJK": "DJK",
    "MTG": "MTG",
    "MTV": "MTV",
    "VFL": "VfL",
    "VFB": "VfB",
    "HG": "HG",
    "HSG": "HSG",
    "SC": "SC",
    "FC": "FC",
    "TG": "TG",
}

_ROMAN_NUMERALS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}

# Angehängte Mannschaftskennung am Ende, z.B. "1M", "2.M", "2.Herren".
_TEAM_SUFFIX_RE = re.compile(r"\s+\d+\.?\s*(m|herren)\.?$", re.IGNORECASE)

_WHITESPACE_RE = re.compile(r"\s+")


def _is_all_caps(name: str) -> bool:
    letters = [c for c in name if c.isalpha()]
    return bool(letters) and all(c == c.upper() for c in letters)


def _title_case_token(token: str) -> str:
    key = token.upper()
    if key in _ABBREVIATIONS:
        return _ABBREVIATIONS[key]
    if key in _ROMAN_NUMERALS:
        return key
    return token.capitalize()


def _title_case_slash_token(token: str) -> str:
    return "/".join(_title_case_token(part) for part in token.split("/"))


def normalize_opponent(raw: str, overrides: dict[str, str] | None = None) -> str:
    """Wandelt einen rohen Gegnernamen von handball.net in die
    Wunsch-Schreibweise um. Die Override-Tabelle wird vor allen Regeln
    geprüft."""
    overrides = overrides or {}
    if raw in overrides:
        return overrides[raw]

    name = _TEAM_SUFFIX_RE.sub("", raw)
    name = _WHITESPACE_RE.sub(" ", name).strip()

    if not _is_all_caps(name):
        return name

    tokens = [_title_case_slash_token(tok) for tok in name.split(" ")]
    return " ".join(tokens)


def _title_case_address_token(token: str) -> str:
    if "-" in token:
        return "-".join(part.capitalize() for part in token.split("-"))
    return token.capitalize()


def clean_handballnet_address(raw: str) -> str:
    """Generische Adressbereinigung für unbekannte Hallen (SPEC.md Abschnitt 9).
    Erwartet den bereits von Backslash-Escapes befreiten LOCATION-Text
    (Kommas nicht mehr escaped)."""
    segments = [s.strip() for s in raw.split(",") if s.strip()]

    if len(segments) >= 2 and segments[-1].lower() in segments[-2].lower():
        segments = segments[:-1]

    cleaned_segments = []
    for segment in segments:
        words = segment.split(" ")
        cleaned_segments.append(" ".join(_title_case_address_token(w) for w in words if w))

    return ", ".join(cleaned_segments) + ", Deutschland"
