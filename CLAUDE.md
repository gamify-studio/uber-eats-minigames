> Reconstructed 2026-07-23 from project memory + repo after the C: drive failure. Best-effort rebuild of the lost CLAUDE.md; verify against the repo and refine.

# uber-eats-minigames

## Session start (read before acting)
Before doing work in this project:
1. Read `plan.md` - North Star: goals, status, task list, decisions. (None present in the repo yet as of this rebuild; create one if work begins.)
2. Check for a session handover; if one exists, resume from it (`/handover pickup`).
3. Skim the "Key docs" below and recent `git log` for current state.
(Memory auto-loads as background context; verify it against the repo before acting.)

## What this is
Gamify-hosted copies of the Uber Eats Side Quest embedded minigames, served via **GitHub Pages** so the Unity build pulls from a repo we control.

- Repo: `gamify-studio/uber-eats-minigames` (public), branch **`master`**.
- Origin story: forked from Jonny Shannon's upstream game repos (`JonnyShan/UberStacker`, `JonnyShan/Multi-View-Screen`) because `ants124` has no push access there (403). Self-hosted here with our own fixes (Back-to-Town + gig scoring). Jonny can still push updates upstream; sync them here.
- **Pushing to `master` = live immediately** via Pages at `https://gamify-studio.github.io/uber-eats-minigames/...` (redeploys ~1-2 min after push). This repo is NOT the Unity build and NOT the S3 test bucket.

The three minigames the build iframes (current names, per memory + recent git log):
- **Food Stacker** = `UberStacker/index.html` (credits the wallet on win)
- **Combo Creator** = `Multi-View-Screen/10ten.html` (merge game on a green board; credits the wallet on win)
- **Path Picker** = `Multi-View-Screen/route-picker.html` (the final / prize game; does NOT credit the wallet - its prize is purely the leaderboard score)

CONFLICT to verify: the repo `README.md` is stale. It lists the three as "Uber Stacker / Route Rush (`route-rush.html`) / 10-Ten (`10ten.html`)". Newer memory (25 Jun 2026) and recent commits use Food Stacker / Combo Creator / **Path Picker** (`route-picker.html`). `route-rush.html` and `route-rush-v2.html` still exist in the tree but appear superseded by `route-picker.html`. Confirm the live iframe URLs in the Unity repo (`SideQuestController.cs` / `QuestController.cs`) before treating any file as the live game.

## Current status
- Repo is committed and clean; branch `master`, tracking `origin`. Recent work (git log) is copy/visual polish across all three games: consistent logos, fluoro Uber Eats bag pieces, green gameplay backgrounds (#06C167), the dollar-symbol coin, scooter/rider placement on win screens, fluoro-bag lives (replaced hearts) in Path Picker, GA4 conversion relay to the host gtag, and campaign end date set to **21 July 2026** (client-confirmed).
- Combo (10ten) recent behaviour: always opens a fresh board (never resumes), always spawns value-1 tiles, resets after finishing.
- Path Picker gating: the final game is meant to be locked behind completing the last story beat, but is deliberately left OPEN/ungated for testing (re-gate before launch). That gate lives in the Unity repo, not here.

## Key docs / where things live
Repo (this project): `C:\Users\Ant\Documents\Claude\Projects\uber-eats-minigames`
- `README.md` - repo overview (STALE game names; see conflict above).
- `UberStacker/` - Food Stacker (`index.html`, `README.md`, `assets/`; `assets/slice.py` regenerates piece PNGs from `pieces-src.png`).
- `Multi-View-Screen/` - holds `10ten.html` (Combo), `route-picker.html` (Path Picker), plus legacy `route-rush.html` / `route-rush-v2.html`, `delivery.html`, `delivery3d.html`, `pack-the-bag.html`, and `docs/superpowers/{plans,specs}/` (moped-game design docs).
- `Multi-View-Screen/assets/uber/README.md` - **STALE** (wrong icon mappings; ignore, see gotchas).

Shared project memory (auto-loads for the broader build, NOT just this repo):
`C:\Users\Ant\.claude\projects\c--Users-Ant-Documents-Claude-Projects-Uber-Eats-Build\memory\` (`MEMORY.md` index + one file per fact). This store covers the WHOLE Uber Eats Side Quest across three repos; scope each fact to the right repo.

Sibling repos in the broader build (not this repo):
- `gamify-studio/UberEatsRider` (Unity, branch `main`) - the main game. Iframes these minigames. Changes go live only after **Matt's WebGL build** (don't build WebGL locally - it crashes the PC).
- `gamify-studio/uber-eats-leaderboard` (private, branch `main`) - serverless AWS leaderboard + prize-signup API. Live base `https://9y63ccaste.execute-api.ap-southeast-2.amazonaws.com`; AWS account 062031384278, region ap-southeast-2, CLI profile `sidequest`. Path Picker POSTs its score + signup here.
- Live WebGL test build (Matt's deploy target): `https://uber-side-quest-test.s3.ap-southeast-2.amazonaws.com/index.html`. Pushing this repo does NOT update that build.

## Hard rules / gotchas
- **Mobile-responsive by default.** Every minigame UI change must scale on real phones (360-414px). Use `clamp()`/`min()`/`vw`/`%`/flex, not fixed px. It's a mobile game; apply this even when not asked.
- **Verify the rendered output, true mobile viewport.** Edge headless clamps the CSS layout viewport to ~476px, so a "360px" screenshot is wrong. Use the CDP harness `node cdpshot.mjs <url> <w> <h> <dsf> <out.png> [waitMs]` (at `...\Uber Eats Build\cdpshot.mjs`) for real 360/390/414. Serve over `http` (e.g. `python -m http.server`) when assets fail under `file://`. Render/measure the real result before saying "done"; don't assert from source.
- **Combo (10ten) icons render on Uber Eats green (`#67BE6B`).** (1) Icon bodies must be fully OPAQUE - transparency only around the outer edge; any internal transparent hole shows the green through as "funny lines" (invisible on dark bg). (2) After ANY icon change, **bump the `?v=N` cache-bust** in `10ten.html` or Pages/browsers serve the stale image. Specs: square RGBA ~420x420 (win bag `6.png` larger), no baked-in level number (game draws 1-6 itself). Current lineup: 1=Coffee, 2=Sushi, 3=Noodles, 4=Flowers, 5=Green Bag, 6=Uber Eats Bag. Don't upscale small icons (adds artifacts). A swapped icon must be a real file on disk (`cp` over `assets/uber/<n>.png`); can't write an image pasted only into chat.
- **`Multi-View-Screen/assets/uber/README.md` is STALE** (lists Burger/Smoothie + wrong file mappings). Ignore it.
- **Back-to-Town + scoring bridge:** each in-game exit button posts `window.parent.postMessage({type:'close'})` to close the overlay, and posts `{type:'gigScore', score}` on win so the Unity wallet credits the real score. Preserve this on any button/win-screen change.
- **"Commit" means commit AND push** (origin is on github.com). Push in the same step. If on the default branch (`master`), follow the standing branch-first rule; never `--no-verify` or skip signing unless asked; new commit, don't amend.
- **Push = deploy here.** Unlike the Unity repo, a push to `master` is immediately live on Pages. Treat every push as a production deploy of the minigames.
- No em-dashes / en-dashes in copy, code comments, or commits (regular hyphens fine); sanitize non-ASCII (Windows curl breaks on it).
- Do the exact task asked; don't substitute a different fix. If blocked, stop and ask.

## People
- **Ant Douglas** - Director at Gamify; owner of this work. Prefers editing locally / not pushing the Unity repo until aligned with Matt (this minigames repo is his to push).
- **Jonny Shannon** - co-Director at Gamify; owns the upstream game repos (`JonnyShan/UberStacker`, `JonnyShan/Multi-View-Screen`) these are forked from. Can sync changes upstream later. `ants124` has no push access to `JonnyShan/*`.
- **Matt** - developer at Gamify; co-devs the Unity `UberEatsRider` repo, pushes to `main`, and does the WebGL builds/deploys (Ant's PC can't build). Not directly this repo, but the consumer of it.
- **Livewire** - white-label partner; minigame/UI copy goes through their legal review (copy is client-owned).
- **Uber** - end client. Signup fields + T&Cs (URL still pending) are Uber-supplied; some decisions await Uber sign-off.
- **Anna Viney** - client-side reviewer whose comments drove the Path Picker gating decision.
- `ants124` is a `gamify-studio` org admin.
