#!/bin/bash
HERE="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
APPDIR="$(dirname "$(dirname "$HERE")")"
export PYTHONPATH="$APPDIR/usr/lib/python3.10/site-packages:$APPDIR/usr/src/extase-em-4r73:$PYTHONPATH"
LIBDIRS=$(find "$APPDIR/usr/lib/python3.10/site-packages" -name "*.libs" -type d 2>/dev/null | tr '\n' ':')
export LD_LIBRARY_PATH="$LIBDIRS$APPDIR/usr/lib:$LD_LIBRARY_PATH"
cd "$APPDIR/usr/src/extase-em-4r73"
exec python3 "$APPDIR/usr/src/extase-em-4r73/main.py" "$@"
