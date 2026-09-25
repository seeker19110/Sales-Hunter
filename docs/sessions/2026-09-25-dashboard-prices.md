# SH-010 implementation checkpoint

Base reviewed: d17d33eae7230aeccc56047db5dd48bf35cdcb1d. Historical audit untouched.

- Red: `PYTHONPATH=src python -m unittest discover -s tests -p test_dashboard_prices.py -v` failed on the original display fields and malformed snapshot.
- Green diagnostic: `PYTHONPATH=src python -m unittest discover -s tests -v`: exit 0, 82 tests; global Python 3.13.5, not a locked environment.
- `PYTHONPATH=src python tools/validate_repo.py`: exit 0 before checkpoint docs; rerun in CI.
- Actual local Chrome/CDP startup succeeds, navigation fails ERR_BLOCKED_BY_ADMINISTRATOR. No browser success claimed locally.
- Browser acceptance is a required separate CI job, not an undiscovered test. It checks exact candidate rows, list/detail prices, Shopee, link/disclosure, viewport overflow and source-script escaping.
- No changes to auth, approval, DB schema, publish or network connector. No live data.

Before merge: inspect exact HEAD CI including browser/metadata, read final diff, verify base unchanged. No auto-merge armed by this checkpoint. PR #36 packaging is independent and still draft. Owner T4 review is still needed for later auth/ADR/publish changes.
