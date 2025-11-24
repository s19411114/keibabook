#!/usr/bin/env python
# Wrapper to avoid running this debug script on import when pytest collects
# it; the actual debug logic is now in `scripts/available_fields_debug.py`.
try:
    from scripts.available_fields_debug import main
except Exception:
    # If the helper script isn't available, keep silent during pytest import
    main = None

if __name__ == '__main__' and main:
    main()
