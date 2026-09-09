from handball_kalender.halls import find_hall, hall_address


def test_find_hall_exact_match(halls):
    hall = find_hall(halls, "Erbacher Berg")
    assert hall is not None
    assert hall.key == "erbacher_berg"


def test_find_hall_substring_match_with_extra_words(halls):
    hall = find_hall(halls, "Flehenberg Gruppe B")
    assert hall is not None
    assert hall.key == "flehenberg"


def test_find_hall_apostrophe_variants(halls):
    assert find_hall(halls, "Franky's Gym").key == "frankys_gym"
    assert find_hall(halls, "Franky’s Gym").key == "frankys_gym"


def test_find_hall_mtc_arena_maps_to_fliethe(halls):
    hall = find_hall(halls, "MTC ARENA WüLFRATH, FORTUNA STR. 30, 42489 WüLFRATH")
    assert hall is not None
    assert hall.key == "fliethe"


def test_find_hall_unknown_returns_none(halls):
    assert find_hall(halls, "Irgendeine andere Halle") is None


def test_hall_address_format(halls):
    fliethe = next(h for h in halls if h.key == "fliethe")
    assert hall_address(fliethe) == "Sporthalle Fliethe, Fortunastraße 30, 42489 Wülfrath, Deutschland"


def test_find_hall_halle_exact_alias_for_fliethe(halls):
    hall = find_hall(halls, "Halle")
    assert hall is not None
    assert hall.key == "fliethe"


def test_find_hall_halle_does_not_match_as_substring(halls):
    """'Halle' ist nur als exakter Treffer hinterlegt (exact_terms), nicht
    als Teilstring -- sonst wuerde er in fremden Hallennamen wie
    'Turnhalle Bonn' faelschlich anschlagen."""
    assert find_hall(halls, "Turnhalle Bonn") is None
