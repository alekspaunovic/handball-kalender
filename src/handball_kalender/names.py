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
    # Vereinskürzel, nicht die Rechtsform "e.V." -- das unterscheidet
    # _RECHTSFORM_RE am Punkt.
    "EV": "EV",
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

# Vereinskürzel, die nicht in der Tabelle stehen, aber offensichtlich Kürzel
# sind: zwei bis vier Buchstaben ohne einen einzigen Vokal. Das trifft BTB,
# LTV, PSV, TSG, BV, FSV, HBD, LTG, HTV, STV, BSDL genauso wie die schon
# gelisteten TV, TSV, HSG -- und kein deutsches Wort. So muss die Tabelle nicht
# bei jedem neuen Gegner wachsen; sie bleibt für die Fälle, die eine Regel
# nicht herleiten kann (TuS, VfL, VfB, EV).
_VOKALE = set("AEIOUÄÖÜY")


def _is_konsonantenkuerzel(token: str) -> bool:
    return (
        2 <= len(token) <= 4
        and token.isalpha()
        and not (set(token.upper()) & _VOKALE)
    )

# Angehängte Mannschaftskennungen am Ende. handball.net hängt sie je Spielklasse
# unterschiedlich an, und weil der Feed bereits nach Team getrennt ist, ist die
# Kennung des Gegners darin redundant. Römische Zahlen bleiben dagegen stehen
# (SPEC.md Abschnitt 6, Regel 5) -- sie unterscheiden echte Mannschaften.
_TEAM_SUFFIX_RES = (
    # Herren und Damen: "1M", "2.M", "2.Herren", "1F", "1D", "2.Damen",
    # "1. Männer", "2. Frauen"
    re.compile(
        r"\s+\d+\.?\s*(?:m|f|d|herren|damen|männer|maenner|frauen)\.?$",
        re.IGNORECASE,
    ),
    # Jugend mit Ziffer: "C1J", "B2", "A1J"
    re.compile(r"\s+[A-E]\d+[JMW]?$", re.IGNORECASE),
    # Jugend kurz: "mA", "mC", "wB"
    re.compile(r"\s+[MW][A-E]$", re.IGNORECASE),
    # Jugend ausgeschrieben: "männl. C-Jugend", "weibl. B-Jugend"
    re.compile(r"\s+(?:männl|weibl|m|w)\.?\s*[A-E]\s*-?\s*Jugend$", re.IGNORECASE),
    # Reine Mannschaftsnummer: "Ohligser TV 1", "MTV 1861 Elberfeld 1".
    # Bewusst nur eine einzelne Ziffer 1-9: zwei- und mehrstellige Zahlen sind
    # Gründungsjahre und gehören zum Namen ("Mainz 05", "TuS 82 Opladen").
    re.compile(r"\s+[1-9]$"),
)

# Rechtsform, die nicht in den Kalendertitel gehört. Der Punkt hinter dem "e"
# ist Pflicht, damit echte Vereinskürzel wie "EV Duisburg" unangetastet
# bleiben, und der vorangehende Zwischenraum, damit nur ein Anhang trifft.
# Steht mitten im Namen, wenn danach noch eine römische Zahl folgt
# ("DJK UNITAS HAAN E.V. II").
_RECHTSFORM_RE = re.compile(r"\s+e\.\s?v\.?(?=\s|$)", re.IGNORECASE)

# Trennzeichen innerhalb eines Wortes. Dahinter muss wieder großgeschrieben
# werden: "WALD-MERSCHEIDER" ist "Wald-Merscheider", nicht "Wald-merscheider",
# und "INTERAKTIV.HANDBALL" ist "Interaktiv.Handball".
_TRENNER_RE = re.compile(r"([-./])")

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
    if _is_konsonantenkuerzel(token):
        return key
    return token.capitalize()


def _title_case_compound(token: str) -> str:
    """Title Case über Trennzeichen hinweg. `str.capitalize` allein würde alles
    hinter dem ersten Buchstaben kleinschreiben."""
    return "".join(
        teil if _TRENNER_RE.fullmatch(teil) else _title_case_token(teil)
        for teil in _TRENNER_RE.split(token)
    )


def _strip_team_suffix(name: str) -> str:
    """Entfernt angehängte Mannschaftskennungen, auch mehrere hintereinander."""
    while True:
        gekuerzt = name
        for muster in _TEAM_SUFFIX_RES:
            gekuerzt = muster.sub("", gekuerzt)
        if gekuerzt == name:
            return name
        name = gekuerzt


def normalize_opponent(raw: str, overrides: dict[str, str] | None = None) -> str:
    """Wandelt einen rohen Gegnernamen von handball.net in die
    Wunsch-Schreibweise um. Die Override-Tabelle wird vor allen Regeln
    geprüft."""
    overrides = overrides or {}
    if raw in overrides:
        return overrides[raw]

    # Reihenfolge: erst die Kennung am Ende, dann die Rechtsform -- sonst steht
    # die Rechtsform bei "… E.V. 1F" der Kennung im Weg.
    name = _strip_team_suffix(raw)
    name = _RECHTSFORM_RE.sub("", name)
    name = _strip_team_suffix(name)
    name = _WHITESPACE_RE.sub(" ", name).strip()

    if not _is_all_caps(name):
        return name

    tokens = [_title_case_compound(tok) for tok in name.split(" ")]
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
