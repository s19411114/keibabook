def safe_log_url(db_manager, url, race_id, tag, status='success'):
    """
    Safe wrapper around db_manager.log_url to avoid exceptions bubbling up.
    """
    try:
        if db_manager:
            db_manager.log_url(url, race_id, tag, status)
    except Exception:
        # Do not propagate logging errors
        pass
