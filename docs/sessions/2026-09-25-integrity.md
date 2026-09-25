# Integrity execution evidence

Baseline: `2522c4db9e168865957d128cab1e597dbb41abb4` after PR #37. Base CI `36140091351` is successful; CD is still a placeholder, not deployment.

- Initial red: `PYTHONPATH=src python -m unittest discover -s tests -p test_integrity_boundaries.py -v`, exit1, 12 tests / 31 failed assertions.
- Authority red: same command, exit1, 16 tests / 4 failures after adding the protocol field but before enforcement. Missing source, forged complete record, rejection with cached receipt, and rejection after SQLite restart all incorrectly sent before the fix.
- Green diagnostic: `PYTHONPATH=src python -m unittest discover -s tests -v`, exit0, 98 tests including the 82 at base. No original test removed/disabled; positive publishing fixtures now persist their approval into the explicit server-configured authority.
- `PYTHONPATH=src python tools/validate_repo.py`, exit0.
- Environment: global Python3.13.5/jsonschema; not an installed locked wheel. Local Git snapshot tree verified equal to upstream `b09885f273fbb634382583c5dcffd6f231759344`; snapshot history is not upstream history.
- Frozen candidate prevents client callbacks from altering receipt identity after validation. A new call always rechecks the current approved record before returning cached success or contacting a client.

Status: local verified, exact HEAD CI pending at checkpoint; T4 human review required even when CI is green. No auto-merge, deploy, real credential or live publication. This does not resolve HTTP identity, immutable history/CAS, per-channel final payload approval or network outcome uncertainty.
