# PR #43 — restore implementation and fix CI

CI-PUB T4, sequential integrator under docs/task-packs/2026-09-26-ci-repair.md. Existing PR target remains #42; #42 depends on #41. No PR in this repair is auto-merged or treated as human-approved.

## Actual baseline

Remote head 1447c44ae1ab44e9e4d6d23779386f0c318716d8, tree e86cec765bdad335b03c332cd973064c78184c22, contains only ADR0010 and ten durable tests above #42. CI 36162837098 and metadata 36162837063 failed. Reconstructed source tree matched upstream. The ten durable tests fail locally with ModuleNotFoundError because publishing implementation was missing from the remote branch. Keep those tests; removing them is not a repair.

## Implementation recovery

Recovered the Python source and integration paths retained in the previous handoff, preserving the original files separately. The parent now includes #41 squash-ancestry synchronization and #42 UTF-8 fixture repair. Added the queue/contracts/schema/worker/fake/recall modules, store transaction hook, channel-specific draft IDs with unchanged channel-agnostic content hash, legacy non-fake direct-send guard, boundary/follow-up tests and installed-wheel smoke covering fake send plus recall.

The recovered handoff was NOT accepted as passing on its prior description: local discovery actually ran 194 tests with two recall errors. RecallService._confirm referred to expected_token without accepting it, and the worker supplied the missing parameter. Fixed the signature and made ownership checks transactional: a worker needs its active unexpired token; unleased confirmation is allowed only while reconciling outcome_unknown. Three new tests reject a stale token, an expired lease and confirmation from pending without a lease. Format-only fixes preserve the ten original durable test assertions and split long SQL literals without changing queries.

## Verification before push

Python 3.13.5 diagnostic discovery: 197 tests OK. Ruff 0.16.7 lint and format checks, validate_repo and git diff --check pass. Global source plus CI-wheel distribution metadata is diagnostic only; uv sync --locked cannot download dependencies in this container. Exact new-head remote CI is still required for Python3.11/3.12 Ubuntu/Windows, Pyright, browser, clean installed wheel and security. Final run IDs belong in the PR conversation after completion, not predicted here.

Other repaired exact heads already have successful CI and metadata: #41 0cff6697 (36200730335/36200730334), #42 28fbd8ce (36201165521/36201165470), #44 23bc6bfb (36201277638/36201277627), #45 41f6821e (36201323368/36201323328). Base remains edec94751e137423338f9d5e3619139df5a770bc. No force pushes or protected-base writes.

## Limits and review

Transport is a separate local SQLite simulator; no real provider is enabled. No network transaction, paid model call, account/secret change, external deployment or user-database migration is performed. The legacy test helper's RAM cache is not advertised as durable delivery. Operator UI, analytics/ledger, production identity and restore drills are separate unfinished epics. Human T4 review of the final #43 diff/ADR0010 and merged dependencies remain required regardless of CI success. Revert through ordinary commits/PR, not by deleting history, receipts or evidence.
