# Stack synchronization after #41 merged

During conflict/CI repair, GitHub showed #41 was squash-merged to bootstrap/base at e458f2130eb661553fb085ae9229a7b04d365c84. The resulting tree f05cfce7f3a00412e612a961dd5b5c36d724f1e7 is identical to the repaired #41 head 0cff6697e8e44563f5c3d4799966f76d7715c950. Base push CI 36201882276 succeeded. This integrator did not execute the merge or provide human approval.

#42 was retargeted to bootstrap/base and GitHub reported a conflict because squash changed ancestry. Resolve with a non-force merge recording e458f213 as the second parent while keeping the already-tested #42 source/test/workflow/dependency tree unchanged. The UTF-8 repair remains present. Prior exact-head CI 36201165521 and metadata 36201165470 passed on 28fbd8ce; the new head must run CI again. #43 inherits this synchronization, not a copy of the old #41 changes.

Scope CI-STACK T2 / CI-VERIFY T1 under docs/task-packs/2026-09-26-ci-repair.md. Source, schemas, old test assertions and review gates unchanged. #42 and #43 retain their own T4/ADR review requirements, with no auto-merge. Final HEAD and CI evidence belong to each PR conversation. No protected-base write, force-push, credential change or live deployment.
