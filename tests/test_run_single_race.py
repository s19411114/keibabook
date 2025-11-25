from scripts.run_single_race import build_race_id


def test_build_race_id_uses_numeric_code():
    rid = build_race_id('20250101', '浦和', 9)
    assert rid.startswith('20250101')
    # Should include numeric code '18' for 浦和
    assert '18' in rid
    assert rid.endswith('09')
