# 10 — Story Structure (publication writeup)

Target publish date: **June 17**. Frozen 14-run matrix is the dataset
(PROTOCOL 1.0-FROZEN, forge-cli 1.0.21). This note is the skeleton + the
locked TL;DR. Every number traces to `results/INDEX.md` and the transcripts.

---

## The locked TL;DR (lead with this verbatim)

**We build and run forge, an automated coding agent, and we pay its token bill — so
before bolting on any external tool that promises to cut that bill, we wanted hard proof
it actually would.** "Context-management" add-ons are sold on a simple claim: attach one
to your agent and it shrinks the tokens it burns, and therefore the cost. We needed that
claim checked against the provider's real billing meter, not the tools' own dashboards.
So we held **forge fixed as the test harness in every run** — the one constant — and
swapped in three of the most visible products in the category, each using a different
strategy: **rtk** (rewrites shell commands to be terse), **headroom** (compresses the
traffic on the wire), and **lean-ctx** (manages a context store and cache). Each ran
inside the same forge pipeline, on the same real software task (plan → implement → review
→ validate → commit), against a baseline of forge running with nothing added. Fourteen
runs, token counts pulled straight from provider billing, under a protocol we froze
before we started. The test is fair and relevant precisely because forge is ours and
never changes: the task is exactly the kind of multi-step coding work these products
target, the three products are leading and genuinely different approaches, and holding
the harness constant is what makes the comparison clean and the only thing worth spending
roughly 76 million tokens of our own money to learn (75,987,395 billed across all 29 runs).
**What we found:** forge's plain baseline already
swung wildly run to run — about 1.9 to 2.7 million tokens — and that random variation
alone was roughly **ten times larger than any tool's effect.** Against that, **none of the
three tools beat running forge with nothing added.** The intuition that a tool shaving
tokens each turn must save money overall doesn't survive contact with an agentic loop:
when headroom compressed the context, the agent ran **more turns** — apparently re-asking
for detail that got trimmed — and in a loop where later, heavier steps cost far more than
earlier ones, those extra turns behave like a loan repaid with interest, erasing the
per-turn saving. rtk and lean-ctx don't even get that far — rtk's touchable surface is
tiny (~1–2.5% of the workload), and lean-ctx *adds* tokens before it saves any, because
the instructions it injects cost more than its cache returns (and the cache never engaged:
each pipeline step is a fresh process, so there was nothing to re-use). The single biggest
saving we saw came from somewhere else entirely — **turning on the provider's own prompt
caching cut cost by ~72%, roughly 14× the best any of these middleware tools managed.**
**We conclude that for a lean, context-frugal harness like forge, context-management
middleware does not reduce token spend and can increase it — not because the products are
bad, but because their real savings are too small to clear ordinary run-to-run noise,
while the actual lever is provider-side caching and keeping the harness's own output
compact.** **So our decision for forge and its users:** we will *not* adopt an external
token/context manager for this pipeline — there's no billing evidence it pays off — and we
recommend instead choosing a model/provider with prompt caching and keeping tool output
lean at the harness level; use the middleware for what it's genuinely good at, not for
token savings here. **Finally, on the teams behind the products:** all three engaged
seriously with the data — **lean-ctx fixed every issue we reported within hours and
shipped releases, headroom reviewed and merged a code change we contributed back, and
rtk's maintainer, though initially skeptical, largely agreed once the specifics were on
the table** — so the benchmark didn't just measure the products, it measurably improved
them.

---

## Narrative spine (7 beats → sections)

1. Why we tested → §1 (motivation = harness-as-invariant; first-person, we pay the bill)
2. What we tested → §2 (the three products, the task, the protocol)
3. Why it's relevant → §2/§3 (real task, leading+distinct products, billing meter not dashboards)
4. What we found → §4–§6 (noise floor, per-arm results, the turn-compounding mechanism)
5. What we conclude → §7 (no net saving; caching is the real lever)
6. What forge recommends → §8 (the decision + the recommendation)
7. How responsive the teams were → §9 (benchmark improved the products)

---

## Section-by-section

### §0 — TL;DR
The locked paragraph above. Standalone; a reader who stops here has the whole story.

### §1 — Why we ran this (motivation = the premise)
- We build and run forge; we pay the token bill. The question is operational, not academic:
  **do we need an external token/context manager bolted onto forge at all?**
- Vendor dashboards say yes; we wanted the provider's billing meter to confirm or deny.
- **Disclosure folded in here, not buried:** forge is our own product and is the *fixed
  element* of the experiment — held constant in every run. That's the premise and the
  thing that makes the comparison clean, not a conflict to apologize for. (Do NOT mention
  lean-ctx usage — free tool, irrelevant, muddles the story. See `04 §4`.)

### §2 — What we tested (setup)
- The three products and their distinct strategies:
  - **rtk** — rewrites shell commands to be terse (acts on command output).
  - **headroom** — compresses request traffic on the wire (acts on every request).
  - **lean-ctx** — context store + cache + injected usage rules (acts on reads/context).
- The task: one real multi-step software change, CART-S01-T01, run as forge's full
  pipeline (plan → review-plan → implement → review-code → validate → writeback → commit).
- The protocol: pre-registered, frozen before runs. Primary metric = **Σ provider-billed
  input tokens per successful run.** N=5 for native baseline (A0), N=3 per arm.
- Why billing-grade: we audit each product's *self-reported* savings against the actual
  bill (vendor-meter audit table). Dashboards are the claim; the bill is the verdict.

### §3 — How to read the result honestly (the noise floor)
- **Lead with the limitation** (it's the most important methodological point):
  the native baseline alone swings **1.89M–2.71M tokens** across 5 identical runs.
- Run-path variance — chiefly the commit phase swinging **23K–927K** — dominates any
  middleware effect by **~1 order of magnitude.**
- Therefore this is a **pre-registered pilot / variance result, not a definitive
  benchmark.** N=3, one task, one pipeline, one model tier. Any honest claim must clear
  that band. (Claim rule: an arm's median outside the A0 band = a real effect.)

### §4 — The headline result
- **No middleware arm achieves a net token reduction that clears the native noise floor.**
- Table (per-arm median, n=3, vs A0 band 1.89M–2.71M / median 2.18M):
  | Arm | Product | Median tokens | vs baseline | Verdict |
  |---|---|---:|---:|---|
  | a2 | headroom v0.23 | 2,571,467 | +17.8% | **inside band** — no better than native |
  | a3 | rtk 0.42.2 | 2,839,459 | +30.1% | **above band** — net increase |
  | a1m | lean-ctx 3.7.5 | 3,015,055 | +38.1% | **above band** — net increase |
- Best case (headroom) merely lands *inside* the band = indistinguishable from running
  nothing, despite genuine ~5–8% wire-level compression.

### §5 — Why each tool nets out the way it does (mechanism, per product)
- **headroom — real compression, eaten by the loop.** Genuine on-wire saving, ledger-exact
  vs the bill (−147K to −238K/run, ~5–8%; R03/R10 reconcile to the token). But it ran
  **more turns** (230, 203 vs ~159 native) at the **lowest tokens-per-turn measured.**
  *The turn-compounding mechanism* (§6) is where the saving goes. Cache/CCR storage never
  engaged (cached=0 every run) — the cache-stabilization suite is structurally invisible on
  our no-cache rail, so we likely *understate* headroom on a cache-priced provider. Say so.
- **rtk — works exactly as designed; surface too small.** 47–79 commands rewritten/run,
  64–76% saved *on the commands it touches* — but those commands are only **~1–2.5% of total
  spend**. Architecture–surface fit, not product quality. The +30% is path variance, not
  rtk cost (rtk has no per-turn token-adding mechanism; the floor run sits at native).
- **lean-ctx — injection cost exceeds cache return; cache never fires.** The maintainer
  fixed everything we first reported (3.7.5: bridge default-on, steering works — 38–64
  ctx_* calls/run). But its session cache is **per-process**, and each forge phase is a
  fresh process → repeat reads only happen *across* phases → **0 cache hits in 7 straight
  runs**, gain meter ~5.8K saved. Meanwhile the MANDATORY usage rules it injects inflate
  context well beyond that. Net: **+38% — it spends more than it saves.** This is a
  harness/architecture mismatch (phase isolation removes its surface), stated as scope.

### §6 — The counter-intuitive core: per-turn savings vs the agentic loop
- The reader's natural objection: *how can a tool that trims tokens every turn not save
  money?* Answer it head-on.
- **Mechanism:** in an agentic loop, trimming context can make the agent **re-ask** for
  detail that was dropped → **more turns**. Extra turns are a **loan repaid with interest**:
  the saving is booked now, the cost arrives later and larger.
- **Where in the loop matters (measured):** forge's phases aren't equal weight — commit and
  validate carry 500K–900K tokens; light phases carry tens of thousands. An extra turn in a
  heavy phase costs 10×+ an extra turn in a light one. So *which* turn inflates changes the
  tokenomics dramatically.
- **Evidence + honesty:** the compression-only v0.24 isolation run had **196 turns with
  zero retrieve calls** — extra turns tracked the compression, not failed look-ups. BUT
  this is a **hypothesis our data is consistent with, not a proven cause** — raw phase
  variance confounds it. Frame as "appears to induce re-fetch turns," not "caused."
- Note: this loan-with-interest mechanism specifically describes **headroom** (the genuine
  per-turn compressor). rtk and lean-ctx fail for the §5 reasons, not this one.

### §7 — What the bill actually rewards (the real lever)
- The biggest saving in the entire study came from **provider-side prompt caching**:
  the Anthropic-model run billed ~72% less (92% cache reads), **~14× the best middleware
  effect**, at ~$1.82 actual vs ~$1.81 projected. 3.3× cheaper than the Claude-Code path
  on the same task.
- Lesson: on this kind of pipeline, tokenomics is won at the **provider/caching layer and
  the harness's own output discipline**, not by inserting context middleware.

### §8 — Our decision + recommendation to forge users
- **Decision:** forge will **not** adopt an external token/context manager for this
  pipeline. No billing evidence it pays off; some evidence it costs.
- **Recommendation:**
  1. Pick a model/provider with **prompt caching** — that's where the order-of-magnitude
     saving lives.
  2. Keep **tool/command output lean at the harness level** — small addressable surface is
     a feature, not a gap.
  3. Use these middleware tools for what they're genuinely good at (rtk's command hygiene,
     headroom's cache-stabilization on a cache-priced rail, lean-ctx's store features) —
     **not** as a token-savings play on a lean harness.

### §9 — The teams behind the products (responsiveness)
- All three maintainers engaged with the data; the benchmark **improved the products**:
  - **lean-ctx (yvgude):** fixed every issue reported, within hours, shipped 3.7.5/3.8.0
    (read-fidelity #404, config liveness). Open question to answer pre-publish: their
    06-13 ask to re-check vs latest release (we hold the frozen-matrix line; fixes landed
    post-freeze). See `09`.
  - **headroom (chopratejas / JerrettDavis):** reviewed and **merged a code change we
    contributed** (PR #823 — compression-only CLI flags). Open thread: turn-count model.
  - **rtk (aeppling):** initially skeptical ("shady," "remove independent"), but most
    substance agreed with or was already in our materials; converged after specifics.
- This is the "external scrutiny makes open-source better" beat — earned, not asserted.

#### Verbatim quotable statements (include in the writeup, attributed; source `09`)

Right-of-reply was given to all three before publication; quote each maintainer
verbatim where a statement is available. Box these as pull-quotes.

- **lean-ctx — yvgude (OWNER), author-provided for the writeup, 2026-06-09:**
  > lean-ctx's savings come from cold-read compression and cached re-reads. On a long-lived
  > context, and especially on cache-priced providers — where both the cached re-reads and the
  > injected prefix ride the provider cache — it nets ahead. On a phase-isolated harness (fresh
  > context per phase) on a non-caching, request-metered provider, the cached-re-read lever has
  > no surface and the injected prefix is re-billed every turn, so it can cost tokens; its
  > addressable share there is a few percent. devasur's decomposition is correct. In response we
  > made the meter state its denominator and the per-turn overhead it injects, added
  > `rules_injection = off` and a minimal surface for hosts that bring their own workflow, and
  > documented the proxy as the way to reach tool output the `ctx_*` tools can't wrap.

  This is the strongest version of the meter-accountability beat: not "the meter lies," but
  "we showed it overstated the net effect, the owner agreed, and the meter was fixed to state
  its denominator." Lead §9 with it.

- **headroom — chopratejas (maintainer), 2026-06-10, on the GitHub issue:**
  > We would like to dig deeper into these results. we do not expect a higher number of turns.
  > we do expect it only if headroom_retrieve is called. We are currently working on multiple
  > fixes … so would like you to hold back on the results — until we have had a chance to
  > validate the environment and settings. we would appreciate your patch offer if you can send
  > us a PR.

  Pair it with the honest tension: our compression-only v0.24 run had **zero retrieve calls
  yet 196 turns**, which sits *against* the maintainer's "turns only inflate if
  headroom_retrieve fires" model — the open technical thread. And we held June 17 firm
  (frozen protocol) while contributing the PR they asked for, which they **merged**.

- **rtk — aeppling (CONTRIBUTOR), 2026-06-12:** no author-approved standalone statement.
  His reply was pointed — verbatim fragments only, quote with care and in context:
  "weird," "shady," and a request to "remove independent." Most of the substance either
  matched our read (he agrees per-turn token-adding "is not possible" — which is our finding,
  not a claim against us) or was already scoped in our materials (variance → n=3+median;
  task surface → our ~2.5% addressable-surface point). Present his words fairly **next to**
  our posted right-of-reply (kept "independent": forge is neutral harness applied identically
  to every arm; forge-compress touches only forge's own store artifacts, held constant across
  all arms; conflict disclosed). If he provides a clean statement before publish, add it here.

### §10 — Limitations & scope (explicit, not defensive)
- One harness, one provider (no cache economics on the rail), one small codebase, one
  model tier, interactive operator protocol, N=3 per arm, single task.
- Claims scoped to **"on this harness."** Explicitly **NOT** "these products don't work" —
  rtk demonstrably worked; the surface was small. headroom compresses for real; the loop
  ate it. lean-ctx's cache works; phase isolation removes its surface.
- Voids published per protocol §5 (orchestrator-steering #41, one provider hang, one
  quota-429) — none implicate middleware.

### §11 — Reproduce it yourself
- Published: `bench/` (Dockerfiles, compose, scripts, pins.env), `notes/`, the frozen
  protocol, analysis jq snippets, raw transcripts. Third-party rebuild = `docker build`
  with only `OLLAMA_API_KEY` supplied. Vendor right-of-reply threads linked.

---

## Total spend (data, for the writeup — billed input tokens, from `results/INDEX.md`)

- **Grand total across all 29 runs: 75,987,395 (~76M).**
- Breakdown:
  - Pilot (6 runs): 17,414,074
  - Exploratory clean (2): 6,625,703
  - **Frozen matrix clean (14): 36,157,905** ← the published dataset
  - Voids / discarded (~5, approx): ~5,432,000
  - ollama-cloud rail subtotal (27 runs): ~65,629,682
  - Cache-priced rail (2 runs, ~92% cache reads — separate accounting): 10,357,713
- Notes: provider-billed **input** tokens (the primary metric); output tokens not separately
  ledgered. Voids are approximate (failed runs we still paid for). The two cache-rail runs
  (c0 Claude Code, a0c) use a different accounting model and are kept separate from the
  primary rail. One real task, run 29 times — ~76M tokens to answer one operational question.

## Assets to finalize before publish
- [ ] Per-arm median chart with the A0 noise band shaded (the one figure that carries §3–§4).
- [ ] Phase-weight chart (commit/validate vs light phases) to make §6 "where in the loop" land.
- [ ] Vendor-meter audit table (self-reported vs billed, per arm).
- [ ] Turn-count vs total-tokens scatter (headroom's extra-turns signal).
- [ ] Resolve lean-ctx #361 06-13 reply (re-check-vs-latest ask) — see `09`.
- [ ] Verbatim pull-quotes laid out in §9 (lean-ctx ✓ author-provided, headroom ✓ issue reply,
      rtk — fragments only; ask aeppling for a clean statement before publish if possible).
- [ ] Secrets audit of transcripts before publishing raw data (auth never in transcripts;
      verify pi-session jsonl).
