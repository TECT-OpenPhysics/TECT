# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: unregistered
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
# === TECT PACKAGE MARKER ===
# Added 2026-04-22 as a companion to `tools/__init__.py`.
# Even though `PDE/` was being resolved as a namespace package on the user's
# Windows / Python 3.12 environment, the resolution is order-sensitive and
# case-insensitive-fs-sensitive. Adding this explicit marker removes that
# fragility and makes the package definition unambiguous to every Python
# launcher we ship in `scripts/`.
# Cross-reference: CHANGELOG 2026-04-22 entry (tools namespace fix).
