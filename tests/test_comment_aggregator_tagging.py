from src.scrapers.comment_aggregator import aggregate_individual_comments


def test_aggregate_individual_comments_tagging():
    horses = [{'horse_num': '1', 'individual_comment': ''}]
    stable = {'1': 'stable comment'}
    prev = {'1': 'prev comment'}
    training = {'1': {'details': [{'comment': 'training comment'}]}}
    point = {'big_upset_horses': [{'horse_num': '1', 'reason': 'odds 1000'}]}
    aggregate_individual_comments(horses, stable, prev, training, point, tag_sources=True)
    combined = horses[0]['individual_comment']
    assert '[stable] stable comment' in combined
    assert '[previous] prev comment' in combined
    assert '[training] training comment' in combined
    assert '[point] odds 1000' in combined
