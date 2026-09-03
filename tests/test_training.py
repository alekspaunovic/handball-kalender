from handball_kalender import training
from handball_kalender.halls import hall_address


def _hall(halls, key):
    return next(h for h in halls if h.key == key)


def test_m3_training_without_ortszusatz_lands_on_fliethe(config, halls, spielerplus_m3):
    vevent = spielerplus_m3["training.76261594"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix)
    assert event.location == hall_address(_hall(halls, "fliethe"))
    assert event.description == ""


def test_m3_training_with_erbacher_berg_resolves_hall(config, halls, spielerplus_m3):
    vevent = spielerplus_m3["training.77001458"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix)
    assert event.location == hall_address(_hall(halls, "erbacher_berg"))
    assert event.summary == "Training 3. Herren - Erbacher Berg"


def test_m3_training_franky_gym_curly_apostrophe(config, halls, spielerplus_m3):
    vevent = spielerplus_m3["training.77001620"]
    event = training.transform(vevent, config.teams["m3"], halls, config.uid_prefix)
    assert event.location == hall_address(_hall(halls, "frankys_gym"))


def test_m2_training_gets_treffpunkt_notiz_10min_before_start(config, halls, spielerplus_m2):
    vevent = spielerplus_m2["training.76020476"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix)
    assert event.dtstart.strftime("%H:%M") == "20:15"
    assert event.description == "Treffpunkt: 20:05"


def test_m2_teamevent_title_and_no_notiz(config, halls, spielerplus_m2):
    vevent = spielerplus_m2["event.2428839"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix)
    assert event.summary == "2. Herren: Teamevent"
    assert event.description == ""


def test_m2_training_with_source_location_keeps_it_instead_of_fliethe(config, halls, spielerplus_m2):
    """SPEC.md Abschnitt 5 (korrigiert): eine von der Quelle gelieferte
    LOCATION ist verlaesslicher als die Standardhalle Fliethe und darf nicht
    ueberschrieben werden, solange sie zu keiner bekannten Halle passt."""
    vevent = spielerplus_m2["training.76020476"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix)
    assert event.location == "Waldschlösschen 39, 42553 Velbert, Deutschland"
    assert event.geo == (51.303683, 7.079041)


def test_m2_auftakt_zur_vorbereitung_keeps_source_location_and_gets_notiz(config, halls, spielerplus_m2):
    """Diese Quelle liefert eine eigene LOCATION (Goethestrasse) und ist per
    UID-Praefix training.* -- bekommt also trotz abweichendem Titel die
    Treffpunkt-Notiz, aber nicht die Standardhalle Fliethe."""
    vevent = spielerplus_m2["training.75635936"]
    event = training.transform(vevent, config.teams["m2"], halls, config.uid_prefix)
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

    assert training.transform(vevent, config.teams["m3"], halls, config.uid_prefix) is None
