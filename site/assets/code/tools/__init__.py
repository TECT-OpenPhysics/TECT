# === TECT PACKAGE MARKER ===
# Trigger/Evidence/Decision (2026-04-22):
#   Trigger : `python -m tools.check_jacobian_symmetry` raised
#             `ModuleNotFoundError: No module named 'tools'` on user Windows /
#             Python 3.12 during v2.5 diagnostic stage [3/4], while the
#             sibling call `python -m PDE.bz_preconditioner` succeeded.
#   Evidence: Both directories lacked `__init__.py`; `PDE/` was resolved as a
#             namespace package but `tools/` was not, almost certainly due to
#             a collision with the Python installation's `Tools/` directory
#             on case-insensitive Windows filesystems (PEP 328 namespace
#             discovery is order-sensitive and case-insensitive-fs-sensitive).
#   Decision: Convert `tools/` into a regular package by adding this empty
#             `__init__.py`. Eliminates the reliance on implicit namespace
#             package discovery. Companion `PDE/__init__.py` added for
#             symmetry and future-proofing.
# Cross-reference: docs/status/TECT-Theory-Currency-Audit-2026-04-22.md (follow-up),
#                  CHANGELOG 2026-04-22 entry, CODE_MANUAL §10.3.
