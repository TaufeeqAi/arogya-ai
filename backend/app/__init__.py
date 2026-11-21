import sys

# Logging must never break a voice turn: force UTF-8 (Hindi) output, replace anything unencodable.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
