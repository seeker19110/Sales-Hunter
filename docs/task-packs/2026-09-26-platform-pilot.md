# Platform integration task pack — 2026-09-26

Owner request: integrate Sales-Hunter into donghanhcungban.org as a separate application.
Base: a78da48eac625621fd22371563eb5a828db2bf39; #42 and #43 are merged.

| Subtask | Tier | Output |
|---|---|---|
| PILOT-TEST | T1 | Read-only/auth/host/persistence regression tests |
| PILOT-WEB | T3 | Isolated WSGI view, no mutations or publishing |
| PILOT-BOUNDARY | T4 | Proposed ADR0011, separate credentials, mandatory Access/TLS gate |
| PILOT-OPS | T4 | Disabled-until-configured service and tunnel templates |
| PILOT-HANDOFF | T2 | Runbook, evidence and DHCB frontend integration contract |

Single integrator, no claimed subagents. Runtime/source tests do not prove deployed state.
No DNS, secret, account, production database or live publication changes. Human review is
required before merge/activation. Rollback is in PLATFORM-PILOT.md; preserve audit history.
