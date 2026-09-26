# #43 final typecheck and stack follow-up

CI 36202272104 on 0fc86ec9f36aa66df1bb8378edafe1ff426c3af9 passed static/format, schema, all four Ubuntu/Windows Python3.11/3.12 unit jobs, browser, clean installed-wheel smoke (including durable fake send/recall), dependency-audit and gitleaks. Metadata 36202272124 passed. Pyright alone failed: tests/test_publication_followup.py replaced FakeTransport.withdraw with a fault-injection function whose positional-or-keyword parameter was named key instead of idempotency_key.

Repair the test wrapper parameter name and its two uses to match the real method contract. Keep the original timeout-after-accept behavior, call-count and reconciliation assertions. No type-ignore or validation exemption. Focused local follow-up suite: six tests OK; Ruff lint and format pass. The original CI failure is preserved as evidence, not reclassified as infrastructure.

The same commit inherits #42 head 3a3846cbdd3de9086934821eff0c6bbab22576f9, which records base e458f213 after #41 squash. Other runtime source is unchanged; parent checkpoint/state docs are reconciled. Final exact-head CI must run again and is recorded in the PR conversation. CI-STACK T2 / CI-VERIFY T1, one integrator; human T4 review remains required for this publishing diff. No merge, force-push, deploy or live transport.
