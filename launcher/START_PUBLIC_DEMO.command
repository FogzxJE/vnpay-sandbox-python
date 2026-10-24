#!/bin/bash
# macOS Finder one-click launcher
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
exec /bin/bash "$HERE/../mac_start.sh" "--public"
