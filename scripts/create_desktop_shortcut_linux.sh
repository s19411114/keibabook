#!/usr/bin/env bash
set -euo pipefail
# Create a Desktop shortcut (.desktop file) for KeibaBook UI on Linux (Zorin/Ubuntu flavors)

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
DESKTOP_DIR=${XDG_DESKTOP_DIR:-$HOME/Desktop}
NAME="KeibaBook"
COMMENT="Start KeibaBook Streamlit UI (safe memory-limited)"
EXEC="$ROOT_DIR/scripts/run_nicegui.sh"
ICON="$ROOT_DIR/docs/assets/icon.png"
ICON_PATH="$ICON"
if [ ! -f "$ICON_PATH" ]; then
  # Optional: fallback icon if not present
  ICON_PATH="/usr/share/pixmaps/keibabook.png"
fi

SHORTCUT_PATH="$DESKTOP_DIR/${NAME}.desktop"

[Desktop Entry]
Type=Application
Name=${NAME}
Comment=${COMMENT}
Exec=${EXEC}
Icon=${ICON}
Terminal=false
Categories=Utility;Development;
EOF
cat > "$SHORTCUT_PATH" <<EOF
[Desktop Entry]
Type=Application
Name=${NAME}
Comment=${COMMENT}
Exec=${EXEC}
Icon=${ICON_PATH}
Terminal=false
Categories=Utility;Development;
EOF
[Desktop Entry]
Type=Application
Name=${NAME}
Comment=${COMMENT}
Exec=${EXEC}
Icon=${ICON}
Terminal=false
Categories=Utility;Development;
EOF

chmod +x "$SHORTCUT_PATH"
echo "Created desktop shortcut: $SHORTCUT_PATH"
#!/usr/bin/env bash
set -euo pipefail
# create_desktop_shortcut_linux.sh
# Create a Desktop shortcut (.desktop file) for the KeibaBook UI on Linux (Zorin/Ubuntu)
# Usage: ./scripts/create_desktop_shortcut_linux.sh --name "KeibaBook UI" --exec "./scripts/run_nicegui.sh" --icon "/path/to/icon.png"

NAME="KeibaBook UI"
EXEC="./scripts/run_nicegui.sh"
ICON=""
DESKTOP_DIR="${HOME}/Desktop"
APP_DIR="${HOME}/.local/share/applications"

while [[ $# -gt 0 ]]; do
  case $1 in
    --name)
      NAME="$2"; shift 2;;
    --exec)
      EXEC="$2"; shift 2;;
    --icon)
      ICON="$2"; shift 2;;
    --desktop-dir)
      DESKTOP_DIR="$2"; shift 2;;
    --app-dir)
      APP_DIR="$2"; shift 2;;
    *)
      echo "Unknown arg $1"; exit 1;;
  esac
done

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
FULL_EXEC="$SCRIPT_DIR/../$EXEC"
FULL_EXEC=$(realpath -m "$FULL_EXEC")

mkdir -p "$DESKTOP_DIR" "$APP_DIR"

FILE_NAME=$(echo "$NAME" | tr ' ' '_' | tr -cd '[:alnum:]_-').desktop
DESKTOP_FILE="$DESKTOP_DIR/$FILE_NAME"
APP_FILE="$APP_DIR/$FILE_NAME"

cat > "$APP_FILE" <<EOF
[Desktop Entry]
Name=$NAME
Exec=bash -lc "cd $(pwd) && $FULL_EXEC"
Terminal=true
Type=Application
EOF

if [ -n "$ICON" ]; then
  echo "Icon=$ICON" >> "$APP_FILE"
fi

chmod +x "$APP_FILE"
cp "$APP_FILE" "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
echo "Created shortcut: $DESKTOP_FILE and $APP_FILE"
