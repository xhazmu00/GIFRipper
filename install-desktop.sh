#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local/share/applications"
mkdir -p "$DEST"
cat > "$DEST/gifripper.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=GIFRipper
Comment=Record and frame-edit GIF animations
Exec=$DIR/run.sh %f
Icon=$DIR/assets/icon.png
Terminal=false
Categories=Graphics;AudioVideo;Video;
MimeType=image/gif;
StartupWMClass=GIFRipper
EOF
chmod +x "$DEST/gifripper.desktop"
echo "Installed: $DEST/gifripper.desktop"
