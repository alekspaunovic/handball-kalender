from handball_kalender import training
from handball_kalender.halls import hall_address


def _hall(halls, key):
    return next(h for h in halls if h.key == key)


def test_m3_training_without_ortszusatz_lands_on_fliethe(config, halls, spielerplus_m3):
    vevent = spielerplus_m3["training.76261594"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.location == hall_address(_hall(halls, "fliethe"))
    assert event.description == ""


def test_m3_training_with_erbacher_berg_resolves_hall(config, halls, spielerplus_m3):
    vevent = spielerplus_m3["training.77001458"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.location == hall_address(_hall(halls, "erbacher_berg"))
    assert event.summary == "Training 3. Herren - Erbacher Berg"


def test_m3_training_franky_gym_curly_apostrophe(config, halls, spielerplus_m3):
    vevent = spielerplus_m3["training.77001620"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.location == hall_address(_hall(halls, "frankys_gym"))


def test_m2_training_gets_treffpunkt_notiz_10min_before_start(config, halls, spielerplus_m2):
    vevent = spielerplus_m2["training.76020476"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.dtstart.strftime("%H:%M") == "20:15"
    assert event.description == "Treffpunkt: 20:05"


def test_m2_teamevent_title_and_no_notiz(config, halls, spielerplus_m2):
    vevent = spielerplus_m2["event.2428839"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.summary == "2. Herren: Teamevent"
    assert event.description == ""


def test_m2_training_with_source_location_keeps_it_instead_of_fliethe(config, halls, spielerplus_m2):
    """SPEC.md Abschnitt 5 (korrigiert): eine von der Quelle gelieferte
    LOCATION ist verlaesslicher als die Standardhalle Fliethe und darf nicht
    ueberschrieben werden, solange sie zu keiner bekannten Halle passt."""
    vevent = spielerplus_m2["training.76020476"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.location == "Waldschlösschen 39, 42553 Velbert, Deutschland"
    assert event.geo == (51.303683, 7.079041)


def test_m2_auftakt_zur_vorbereitung_keeps_source_location_and_gets_notiz(config, halls, spielerplus_m2):
    """Diese Quelle liefert eine eigene LOCATION (Goethestrasse) und ist per
    UID-Praefix training.* -- bekommt also trotz abweichendem Titel die
    Treffpunkt-Notiz, aber nicht die Standardhalle Fliethe."""
    vevent = spielerplus_m2["training.75635936"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.summary == "2. Herren: Auftakt zur Vorbereitung"
    assert event.location == "Goethestraße 23, 42489 Wülfrath, Deutschland"
    assert event.description.startswith("Treffpunkt: ")


def test_spiel_uid_is_discarded(config, halls):
    from icalendar import Event as IEvent
    from datetime import datetime
    from zoneinfo import ZoneInfo

    vevent = IEvent()
    vevent.add("UID", "spiel.123")
    vevent.add("SUMMARY", "Training")
    vevent.add("DTSTART", datetime(2026, 1, 1, 10, 0, tzinfo=ZoneInfo("Europe/Berlin")))
    vevent.add("DTEND", datetime(2026, 1, 1, 12, 0, tzinfo=ZoneInfo("Europe/Berlin")))

    assert training.transform(vevent, config.teams["m3"], halls, config.uid_prefix, config.spielerplus_uid_prefixes) is None


def test_m3_training_halle_ortszusatz_is_treated_as_no_ortszusatz(config, halls, spielerplus_m3):
    """SpielerPlus gibt den Ort teils explizit als 'Halle' an, gemeint ist
    die Standardhalle Fliethe -- das darf nicht im Titel auftauchen."""
    vevent = spielerplus_m3["training.78506613"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert event.summary == "Training 3. Herren"
    assert event.location == hall_address(_hall(halls, "fliethe"))


def test_game_uid_is_discarded_regardless_of_positive_list(config, halls, spielerplus_m2):
    """Echtes VEVENT mit Praefix 'game.' aus dem realen SpielerPlus-Feed --
    Spiele kommen aus handball.net und duerfen nicht doppelt landen."""
    vevent = spielerplus_m2["game.13373164"]
    assert training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes) is None


def test_absence_uid_is_discarded_regardless_of_positive_list(config, halls, spielerplus_m2):
    """Echtes VEVENT mit Praefix 'absence.' aus dem realen SpielerPlus-Feed."""
    vevent = spielerplus_m2["absence.8595485"]
    assert training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes) is None


def test_unknown_uid_prefix_is_discarded_and_logged(config, halls, spielerplus_m2, caplog):
    """Echtes VEVENT mit dem unbekannten Praefix 'tournament.' -- muss
    verworfen UND als Warnung geloggt werden, damit nichts stillschweigend
    verlorengeht."""
    vevent = spielerplus_m2["tournament.2055844"]
    with caplog.at_level("WARNING"):
        result = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix, config.spielerplus_uid_prefixes)
    assert result is None
    assert any("tournament.2055844" in record.message for record in caplog.records)


def test_only_training_and_event_uids_survive_a_mixed_feed(config, halls):
    """Positivliste (SPEC.md Abschnitt 2): von allen vier realen Praefixen
    ueberleben nur training. und event."""
    from icalendar import Event as IEvent
    from datetime import datetime
    from zoneinfo import ZoneInfo

    def _vevent(uid, summary="Training"):
        v = IEvent()
        v.add("UID", uid)
        v.add("SUMMARY", summary)
        v.add("DTSTART", datetime(2026, 1, 1, 10, 0, tzinfo=ZoneInfo("Europe/Berlin")))
        v.add("DTEND", datetime(2026, 1, 1, 12, 0, tzinfo=ZoneInfo("Europe/Berlin")))
        return v

    team = config.teams["m3"]
    kept = [
        prefix
        for prefix in ("training", "event", "game", "absence")
        if training.transform(
            _vevent(f"{prefix}.1"), team, halls, config.uid_prefix, config.spielerplus_uid_prefixes
        )
        is not None
    ]
    assert kept == ["training", "event"]
