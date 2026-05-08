#!/usr/bin/env python3
# =====================================================================
# sync_toe_from_states.py — DEPRECATED (renamed 2026-05-07).
# This file forwards to sync_toe_from_status.py for backward compatibility.
# Direct callers should switch to the new name; this stub will be removed
# after one snapshot cycle.
# =====================================================================
import sys
from pathlib import Path

print("[sync-toe-from-states] DEPRECATED: forwarding to sync_toe_from_status.py.",
      file=sys.stderr)
print("[sync-toe-from-states] Update your invocation to "
      "Codes/tools/sync_toe_from_status.py.", file=sys.stderr)

# Forward import + main()
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_toe_from_status import main as _main
raise SystemExit(_main())
