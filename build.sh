#!/bin/bash
# Build script — TOS 7 Deb application package (single-package mode)
set -e
APPID="tos7-app-19-algernon"
PLATFORM="${1:-x86_64}"
# 找一个「真的能跑」的 Python —— Windows 上 python3 可能是应用商店占位符
PY=""
for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "pass" >/dev/null 2>&1; then
        PY="$c"; break
    fi
done
if [ -z "$PY" ]; then
    echo "ERROR: a working python3/python is required" >&2
    exit 1
fi

"$PY" tools/mkdeb.py --appid "$APPID" --mode single --platform "$PLATFORM"
