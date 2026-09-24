"""SPEC-ADMIN.md Abschnitt 9: overrides.json darf das Erzeugen der Feeds
niemals verhindern."""

import logging

from handball_kalender import overrides


def test_missing_file_gives_empty_overrides_and_warns(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        result = overrides.load(tmp_path / "overrides.json")

    assert result.hidden == set()
    assert result.custom == []
    assert result.included == set()
    assert "fehlt" in caplog.text


def test_broken_json_gives_empty_overrides_and_warns(tmp_path, caplog):
    path = tmp_path / "overrides.json"
    path.write_text('{"hidden": [', encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        result = overrides.load(path)

    assert result.hidden == set()
    assert result.custom == []
    assert result.included == set()
    assert "JSON" in caplog.text


def test_wrong_types_are_ignored_field_by_field(caplog):
    with caplog.at_level(logging.WARNING):
        result = overrides.parse({"hidden": "tbw-m2-spiel-1", "custom": {}, "included": ["a"]})

    assert result.hidden == set()
    assert result.custom == []
    assert result.included == {"a"}


def test_custom_entry_without_required_fields_is_skipped(caplog):
    vollstaendig = {
        "uid": "tbw-custom-a1b2c3",
        "summary": "Mannschaftsabend",
        "dtstart": "2026-11-14T19:00:00",
        "dtend": "2026-11-14T23:00:00",
    }
    with caplog.at_level(logging.WARNING):
        result = overrides.parse(
            {"custom": [vollstaendig, {"uid": "tbw-custom-kaputt", "summary": "Ohne Zeit"}]}
        )

    assert [entry["uid"] for entry in result.custom] == ["tbw-custom-a1b2c3"]
    assert "tbw-custom-kaputt" in caplog.text


def test_full_example_from_the_spec_parses():
    result = overrides.parse(
        {
            "version": 1,
            "hidden": ["tbw-m2-spiel-380455"],
            "custom": [
                {
                    "uid": "tbw-custom-a1b2c3",
                    "summary": "Mannschaftsabend",
                    "dtstart": "2026-11-14T19:00:00",
                    "dtend": "2026-11-14T23:00:00",
                    "all_day": False,
                    "location": "Sporthalle Fliethe, Fortunastraße 30, 42489 Wülfrath, Deutschland",
                    "description": "",
                    "created": "2026-09-24T18:00:00Z",
                }
            ],
            "included": ["tbw-a-jugend-spiel-661234"],
        }
    )

    assert result.hidden == {"tbw-m2-spiel-380455"}
    assert result.included == {"tbw-a-jugend-spiel-661234"}
    assert result.custom[0]["summary"] == "Mannschaftsabend"
