from src.scrapers.comment_aggregator import aggregate_individual_comments


def test_aggregate_individual_comments_dedupe():
    horses = [{'horse_num': '1', 'individual_comment': ''}]
    stable = {'1': 'same comment'}
    prev = {'1': 'same comment'}
    training = {'1': {'details': [{'comment': 'training comment'}, {'comment': 'same comment'}]}}
    point = {'big_upset_horses': [{'horse_num': '1', 'reason': 'training comment'}]}
    aggregate_individual_comments(horses, stable, prev, training, point)
    combined = horses[0]['individual_comment']
    # 'same comment' should appear only once, and order should preserve first occurrence
    assert combined.count('same comment') == 1
    assert 'training comment' in combined
