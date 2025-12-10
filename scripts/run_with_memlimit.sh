#!/usr/bin/env bash
set -eu
# Wrapper to run a command with virtual memory (address space) limit using prlimit
# Usage: ./scripts/run_with_memlimit.sh 6G -- python scripts/run_scraper.py --race_id=...

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <limit> -- <command>..." >&2
  exit 2
fi
LIMIT="$1"
shift
if [ "$1" != "--" ]; then
  echo "Separator '--' expected" >&2
  exit 2
fi
shift
CMD=("$@")

# Convert common units to bytes for prlimit if necessary (prlimit supports suffixes but keep simple)
echo "Running: prlimit --as=$LIMIT -- ${CMD[*]}"
exec prlimit --as=$LIMIT -- "${CMD[@]}"
#!/usr/bin/env bash
# Wrapper to run a command with an address-space (virtual memory) limit via prlimit.
# Usage: ./scripts/run_with_memlimit.sh 6G -- python scripts/run_scraper.py --race_id=20251206... (prlimit args then command)

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <mem-limit> -- <command...>"
  echo "Example: $0 6G -- python scripts/run_scraper.py --race_id=..."
  exit 2
fi

MEMLIMIT="$1"
shift
if [ "$1" != "--" ]; then
  echo "Missing -- separator after mem-limit" >&2
  exit 2
fi
shift

# Use /usr/bin/prlimit or command -v
PRLIMIT_BIN=$(command -v prlimit || true)
if [ -z "$PRLIMIT_BIN" ]; then
  echo "prlimit not found. On some systems, install 'util-linux' or use setrlimit in Python." >&2
  exit 1
fi

# run with AS limit
exec "$PRLIMIT_BIN" --as="${MEMLIMIT}" -- "$@"
