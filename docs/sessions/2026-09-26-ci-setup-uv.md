# PR #44 — setup-uv CI/metadata repair

CI-DEPS T1, branching A on the existing Dependabot branch. Reviewed baseline dfd04f8f1ad4919f1783ec6132e5f8402ea8eedd: the only dependency change is eight setup-uv pins in ci.yml, from bec219d24cd3e171d82865faccec33120bb574f4 (v10.1.0) to c18668ad3cf93ea998bef934396af7bb5c839dc7 (v10.2.0). All permissions, test jobs and quality dependencies are unchanged.

Baseline CI 36198806100 passed. PR policy 36198806883 failed specifically at the CHANGELOG step (job 108280651748). Repair supplies an actual changelog entry and this checkpoint, not a no-changelog exemption. A non-force merge sync includes current auth base edec94751e137423338f9d5e3619139df5a770bc; runtime source remains byte-identical to that base. PR #39 is already merged, independent T4 epics #41/#42/#43 are not imported here.

Allowed files: original dependency diff, changelog, this session. No security/test gate is removed. Exact new-head CI and metadata must pass before integration; final run IDs are recorded in the PR conversation. User requested conflict/CI repair, not a production operation. No deployment or automatic approval. Rollback by ordinary revert commit on this branch.
