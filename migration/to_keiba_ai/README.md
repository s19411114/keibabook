# Migration to keiba-ai

This folder collects files, scripts, and documentation that we propose to move from keibabook to the keiba-ai project.

Purpose:
- Group historical Netkeiba collection tools, batch pedigree harvesters, and track bias calculations that belong to keiba-ai.
- Provide a clear migration manifest and consolidation suggestions for the keiba-ai maintainers.

What's here:
- A list of candidate files (manifest.md) describing why each file is selected.
- Copies of scripts and modules that require attention (src/scrapers/*, src/utils/track_bias.py, run_pedigree.py, run_pedigree_safe.py, etc.).

Notes:
- Files are copied here for review; the originals in the keibabook repo remain unchanged for now.
- After review and approval, these files should be moved into the keiba-ai repo and removed from keibabook where appropriate.

Contact: s19411114 (repo owner)
