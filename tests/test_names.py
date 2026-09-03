import pytest

from handball_kalender.names import clean_handballnet_address, normalize_opponent


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Lüttringhauser TV", "Lüttringhauser TV"),
        ("NEUSSER HV 1M", "Neusser HV"),
        ("DJK GRÜN WEISS WERDEN 2.M", "DJK Grün Weiss Werden"),
        ("SSG WUPPERTAL/HSV WUPPERTAL", "SSG Wuppertal/HSV Wuppertal"),
        ("TB WÜLFRATH IV", "TB Wülfrath IV"),
        ("TUS LINTFORT", "TuS Lintfort"),
        ("MTG Horst Essen", "MTG Horst Essen"),
    ],
)
def test_normalize_opponent_examples(raw, expected):
    assert normalize_opponent(raw, {}) == expected


def test_normalize_opponent_override_wins_before_rules():
    overrides = {"NEUSSER HV 1M": "Neusser Handverein"}
    assert normalize_opponent("NEUSSER HV 1M", overrides) == "Neusser Handverein"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "BOCKMüHLE, MERCATORSTR., 45143 ESSEN, 45143 ESSEN",
            "Bockmühle, Mercatorstr., 45143 Essen, Deutschland",
        ),
        (
            "MATARé-GYMNASIUM, NIEDERDONKER STR. 34, 40667 MEERBUSCH, 40667 MEERBUSCH",
            "Mataré-Gymnasium, Niederdonker Str. 34, 40667 Meerbusch, Deutschland",
        ),
    ],
)
def test_clean_handballnet_address_examples(raw, expected):
    assert clean_handballnet_address(raw) == expected
