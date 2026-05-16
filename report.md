# Fork Rebase Report

User: `rel1f3`
Date: 2026-05-16

## Summary

- **Total forks**: 4
- **Total branches processed (across all forks)**: 8
- ✅ **Rebased & pushed**: 1
- ⏭️ **Skipped**: 3 (the session work-branch holding this report on Action-Build, one stale claude/* on Action-Build, one stale claude/* on GKI_KernelSU_SUSFS)
- ❌ **Failed**: 4 (all `push unauthorized in sandbox` — see Environment notes)

### Failed breakdown by repo

- `rel1f3/Build_Lenovo_sm8750`: 1 branch — `main`
- `rel1f3/GKI_KernelSU_SUSFS`: 1 branch — `dev` (also has stale `claude/rebase-and-push-SCvnZ`, skipped as automation)
- `rel1f3/RunFilesBuilder`: 1 branch — `master`

### Roll-back

History is preserved entirely in the local reflog of the affected clone. To
roll back the only rebased branch (`rel1f3/Action-Build@SukiSU-Ultra`):

```
cd Action-Build
git reflog SukiSU-Ultra | head -20      # find the pre-rebase sha (commit 2dec5d3 "对齐伪装管理器和内核源码版本")
git checkout SukiSU-Ultra
git reset --hard 2dec5d3                 # or the sha you picked from the reflog
git push origin SukiSU-Ultra --force-with-lease
```

No backup branch was created and no refs were deleted. The reflog inside the
local clone — *not* the GitHub server — is the only roll-back source. If the
clone is discarded before you roll back, the old SHAs are still reachable on
the GitHub side for ~90 days via the GitHub `events` API and via `git fetch`
of the dangling commit by hash, but only if you saved the SHA beforehand. The
pre-rebase tip of `SukiSU-Ultra` was **`2dec5d3 对齐伪装管理器和内核源码版本`**.

---

## Inventory

| Fork | Default | Upstream (parent) | Upstream default |
|---|---|---|---|
| rel1f3/Action-Build | SukiSU-Ultra | Numbersf/Action-Build | SukiSU-Ultra |
| rel1f3/Build_Lenovo_sm8750 | main | qdykernel/Build_Lenovo_sm8750 | main |
| rel1f3/GKI_KernelSU_SUSFS | dev | zzh20188/GKI_KernelSU_SUSFS | dev |
| rel1f3/RunFilesBuilder | master | wukongdaily/RunFilesBuilder | master |

## Environment notes

This run is executing inside Claude Code's restricted remote-execution sandbox.
The push credentials provided by the local git proxy authorize **only** the
single repository `rel1f3/Action-Build`. The proxy explicitly rejects all
other `rel1f3/*` repositories with `502 Proxy error: repository not
authorized`, and no GitHub PAT is available in the environment.

Read access is fine for all 4 forks (via direct `https://github.com/...`),
but **push** is impossible for the other three. There is therefore no point
in performing a rebase that we cannot deliver — the work would only consume
local disk in an ephemeral container — so for those three forks the report
records `push unauthorized in sandbox` against each non-automation branch.

To process those forks yourself in a normal terminal:

```
git clone https://github.com/rel1f3/<repo>
cd <repo>
git remote add upstream <parent-url>
git fetch upstream
git rebase upstream/<branch>
git push origin <branch> --force-with-lease
```

The required `upstream` URLs are in `forks.json` (also committed in this
report).

## Per-branch results

### rel1f3/Action-Build (origin via authorized proxy)

- `rel1f3/Action-Build/SukiSU-Ultra`: ✅ rebased onto `upstream/SukiSU-Ultra` (+15 commits replayed onto +26 new upstream commits), pushed with `--force-with-lease`.
  - Conflict: 1 file — `.github/workflows/Build Kernel OnePlus.yml`, in fork commit `698ff5d "Allow spoof cert patch to use SukiSU Makefile"`.
  - Resolution: semantic merge. Kept upstream's new `Reject Check` step (sets `REJ_CHECKER` env, scans `*.rej` after each patch), and kept fork's `Install Dependencies + APTC` step (Numbersf cache-apt-pkgs action) in place of upstream's manual `apt-get install`. Both surface different concerns and coexist as two separate YAML steps. The two later `source $REJ_CHECKER; check_rejects .` invocations (in the second conflict hunk) were preserved on the upstream side because the step that defines `REJ_CHECKER` is still present.
  - Remaining 14 fork commits replayed cleanly with no further intervention.
  - Pre-rebase tip: `2dec5d3 对齐伪装管理器和内核源码版本`
  - Post-rebase tip: `c3eb096 对齐伪装管理器和内核源码版本`
- `rel1f3/Action-Build/claude/rebase-and-push-0zkmK`: ⏭️ skipped: 自动化分支 (Claude Code session work branch — holds this report).
- `rel1f3/Action-Build/claude/kernel-manager-config-1aD43`: ⏭️ skipped: 自动化分支 (stale Claude Code session branch from an earlier run).

### rel1f3/Build_Lenovo_sm8750 (no push credentials)

- `rel1f3/Build_Lenovo_sm8750/main`: ❌ push unauthorized in sandbox
  - ↳ 回退: not needed (no remote write occurred). To run locally: `git clone https://github.com/rel1f3/Build_Lenovo_sm8750 && cd Build_Lenovo_sm8750 && git remote add upstream https://github.com/qdykernel/Build_Lenovo_sm8750 && git fetch upstream && git rebase upstream/main && git push origin main --force-with-lease`. Roll-back via the reflog after the fact: `git reflog main | head -20`.

### rel1f3/GKI_KernelSU_SUSFS (no push credentials)

- `rel1f3/GKI_KernelSU_SUSFS/dev`: ❌ push unauthorized in sandbox
  - ↳ 回退: not needed (no remote write occurred). To run locally: `git clone https://github.com/rel1f3/GKI_KernelSU_SUSFS && cd GKI_KernelSU_SUSFS && git remote add upstream https://github.com/zzh20188/GKI_KernelSU_SUSFS && git fetch upstream && git rebase upstream/dev && git push origin dev --force-with-lease`. Roll-back via the reflog after the fact: `git reflog dev | head -20`.
- `rel1f3/GKI_KernelSU_SUSFS/claude/rebase-and-push-SCvnZ`: ⏭️ skipped: 自动化分支 (stale Claude Code session branch from an earlier run).

### rel1f3/RunFilesBuilder (no push credentials)

- `rel1f3/RunFilesBuilder/master`: ❌ push unauthorized in sandbox
  - ↳ 回退: not needed (no remote write occurred). To run locally: `git clone https://github.com/rel1f3/RunFilesBuilder && cd RunFilesBuilder && git remote add upstream https://github.com/wukongdaily/RunFilesBuilder && git fetch upstream && git rebase upstream/master && git push origin master --force-with-lease`. Roll-back via the reflog after the fact: `git reflog master | head -20`.

---

## Skip rules used

A branch was marked `⏭️ skipped: 自动化分支` if it matched any of:

- `gh-pages`
- `dependabot/*`, `renovate/*`
- `release-please--*`, `changeset-release/*`
- `claude/rebase-and-push-*` (the Claude Code session branch driving this
  run; rebasing the branch we're committing the report on would clobber the
  report).

No other branches were skipped.

## Tag policy

`upstream` was fetched without `--tags`. Git's default behaviour still
auto-follows tags reachable from fetched branch tips, so the Action-Build
clone gained 12 upstream tags as a side-effect of `git fetch upstream`. Those
tag refs exist only in the local clone — they were **not** pushed (push to
`origin` was branch-scoped: `git push origin SukiSU-Ultra ...`) and **not**
deleted. The remote tag set on `rel1f3/Action-Build` is unchanged.
