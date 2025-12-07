from src.scrapers.comment_aggregator import aggregate_individual_comments


def test_aggregate_individual_comments_basic():
    horses = [{'horse_num': '1', 'individual_comment': ''}, {'horse_num': '2', 'individual_comment': ''}]
    stable = {'1': 'stable comment 1'}
    prev = {'2': 'prev comment 2'}
    training = {'1': {'details': [{'comment': 'training 1a'}, {'comment': 'training 1b'}]}, '2': {'details': []}}
    point = {'big_upset_horses': [{'horse_num': '2', 'reason': 'odds 1000'}]}
    aggregate_individual_comments(horses, stable, prev, training, point)
    assert 'stable comment 1' in horses[0]['individual_comment']
    assert 'training 1a' in horses[0]['individual_comment']
    assert 'prev comment 2' in horses[1]['individual_comment']
    assert 'odds 1000' in horses[1]['individual_comment']
