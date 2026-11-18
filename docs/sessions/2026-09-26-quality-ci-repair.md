# #42 CI repair — explicit fixture encoding

Baseline head ef275d52de12516f556c482f75a7c9574eff45f2, failed CI 36162253478. Windows job 108161406455 ran 162 tests and reported 19 errors: both shared fixture loaders called Path.read_text without an encoding; Windows cp1252 could not decode the Vietnamese UTF-8 observation fixture. Linux and the other quality jobs passed. This was not an infrastructure retry case.

Fix: explicitly use UTF-8 in tests/test_deal_quality.py and tests/test_grounded_flow.py; do not modify fixture data or assertions. Two new tests in tests/test_fixture_encoding.py simulate a cp1252 default and compare the complete loaded values. Regression red: 2 tests/2 UnicodeDecodeError errors; green discovery: 164 tests OK, Ruff lint/format and validate_repo OK on local Python3.13.5. Local source+distribution metadata diagnostics are not locked runtime evidence; Windows/browser/wheel/security must pass on the exact new remote head.

The branch also inherits #41's non-force synchronization with squash-merged #39. Its base remains #41, not bootstrap/base while the data dependency is unmerged. Human T4 review/ADR gates remain; no auto-merge, no live publication, no production migration or secrets. Historical audit evidence is unchanged. Final HEAD/run IDs are recorded in the PR conversation.
