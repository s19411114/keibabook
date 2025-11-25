from src.utils.venue_manager import VenueManager


def test_normalize_venue_name_basic():
    assert VenueManager.normalize_venue_name('浦和') == '浦和'
    assert VenueManager.normalize_venue_name('浦和競馬場浦和記念') == '浦和'
    assert VenueManager.normalize_venue_name('開催日程') is None


def test_get_venue_numeric_code():
    assert VenueManager.get_venue_numeric_code('浦和') == '18'
    assert VenueManager.get_venue_numeric_code('福島') == '03'
    assert VenueManager.get_venue_numeric_code('Unknown') is None
