from src.utils.logger import get_logger

logger = get_logger(__name__)

def aggregate_individual_comments(horses, stable_comment_data, previous_race_comment_data, training_data, point_data, tag_sources: bool = False):
    """
    Combine comments from shutuba/training/stable/previous/point pages into individual_comment.
    Avoid duplicate comment fragments while preserving order. Optionally tag comment sources.

    Args:
        horses: list of horse dicts
        stable_comment_data: dict
        previous_race_comment_data: dict
        training_data: dict
        point_data: dict
        tag_sources: bool - if True, prepends source tags like [stable], [prev], [training], [point]
    """

    def point_reasons_for(horse_num):
        reasons = []
        if not point_data:
            return reasons
        for key in ['big_upset_horses', 'strong_run_hints', 'ai_pedigree_picks', 'power_track_horses', 'board_horses']:
            for item in point_data.get(key, []) or []:
                if item.get('horse_num') == horse_num:
                    r = item.get('reason') or item.get('odds') or ''
                    if r:
                        reasons.append(str(r))
        return reasons

    for horse in horses:
        horse_num = horse.get('horse_num')
        parts = []
        seen = set()

        def maybe_append(s):
            if not s:
                return
            if s in seen:
                return
            seen.add(s)
            parts.append(s)

        raw_count = 0
        # stable
        if horse_num and (horse_num in stable_comment_data):
            val = stable_comment_data.get(horse_num, "")
            raw_count += 1 if val else 0
            if tag_sources and val:
                maybe_append(f"[stable] {val}")
            else:
                maybe_append(val)
        # previous
        if horse_num and (horse_num in previous_race_comment_data):
            val = previous_race_comment_data.get(horse_num, "")
            raw_count += 1 if val else 0
            if tag_sources and val:
                maybe_append(f"[previous] {val}")
            else:
                maybe_append(val)
        # training comments
        if horse_num and training_data and (horse_num in training_data):
            td = training_data.get(horse_num, {})
            details = td.get('details', [])
            for d in details:
                if d and d.get('comment'):
                    val = d.get('comment')
                    raw_count += 1
                    if tag_sources:
                        maybe_append(f"[training] {val}")
                    else:
                        maybe_append(val)
        # point-derived reasons
        if horse_num:
            for r in point_reasons_for(horse_num):
                raw_count += 1
                if tag_sources:
                    maybe_append(f"[point] {r}")
                else:
                    maybe_append(r)

        combined = ' '.join(parts).strip()
        horse['individual_comment'] = combined

        # Logging: show if duplicates were filtered
        final_count = len(parts)
        if raw_count > final_count:
            logger.info(f"aggregator: horse={horse_num} - raw_parts={raw_count}, unique_parts={final_count}")
