# === TECT PACKAGE MARKER ===
# Added 2026-04-22 as a companion to `tools/__init__.py`.
# Even though `PDE/` was being resolved as a namespace package on the user's
# Windows / Python 3.12 environment, the resolution is order-sensitive and
# case-insensitive-fs-sensitive. Adding this explicit marker removes that
# fragility and makes the package definition unambiguous to every Python
# launcher we ship in `scripts/`.
# Cross-reference: CHANGELOG 2026-04-22 entry (tools namespace fix).
