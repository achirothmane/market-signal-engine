# Market Signal Engine — inherited product baseline

**Date:** 2026-10-10
**Project owner:** achirothmane
**Status:** imported upstream code on main; static baseline PASS; runtime and customer outcomes not yet proven.
**Upstream:** [dgtlmoon/changedetection.io](https://github.com/dgtlmoon/changedetection.io), release `0.60.8`.
**Original upstream commit:** `09881f8b26aa01a2be66c5f63daf54a79a42b6bd`.
**Attribution and Git-history rewrite:** [UPSTREAM.md](../UPSTREAM.md). Original GitHub upstream workflows were excluded when importing, due to restricted push permissions; imported commit IDs are different. GitHub reports `fork: false` (independent source derivative, **not** a GitHub-network fork).

## Why this codebase

Do not rebuild upstream watches, extraction, diff history, UI, notification routing, backup, API, or scheduling. Our intended first use is **internal monitoring of permitted public pages** across product prices, engineering releases, licenses, software capabilities, regulations where permitted, and market signals. A paid product or niche is **not** selected. This source is not differentiated merely by new branding, AI summaries, alerts, scraping or a dashboard; the upstream already has much of that.

## Read-first source landmarks

- `changedetectionio/`: full inherited Python application.
- `changedetection.py`: CLI entrypoint.
- `Dockerfile` and `docker-compose.yml`: upstream deployment assets. **Note:** the inherited compose file pulls the upstream hosted container image; it does **not** build this fork's source automatically. A passing `docker compose up` is therefore not proof of our source.
- `docs/api-spec.yaml`: inherited OpenAPI description.
- `LICENSE`: Apache-2.0. Keep all attribution/notice and audit third-party deps before any redistributions.
- `.github/workflows/market-signal-baseline.yml`: our lean Python syntax / lint / API validation, no deployment.
- `.github/workflows/market-signal-runtime-smoke.yml`: separately bounded local startup check; pass/fail must come from its actual run.

## Engineering strategy

1. Inherited source first. No parallel rewrites in Go, Rust or TypeScript just to create activity.
2. Reproduce an unmodified local startup and fetch/UI smoke via ephemeral GitHub runner (not always-on hosting); capture exact source commit, output and cost/time.
3. Set up one self-owned or expressly authorized synthetic page fixture; verify that changes produce recorded diffs without duplicate/spurious alerts. Respect robots, rates, copyright/data rights, local law and site access controls.
4. Only after a working need is shown, export a stable `source change -> timestamp -> old/new values -> content hash -> origin/rights -> confidence/UNKNOWN` event into Data Engine; composition requires a proven consumer.
5. Use it ourselves to accumulate evidence/history. Make a commercial claim only after Competitive Freshness Gate establishes buyer value beyond upstream and established paid rivals, plus sustainable payment/delivery economics.

## Budget and operating boundary

No required paid LLM, proxy, hosting, advertising or new hardware. Static CI and short-lived runner checks do not equal persistent monitoring; reliable 24/7 service will need explicitly approved compute/storage, uptime and security work. Do not ingest sensitive or private customer content into public build logs. Not approved for autonomous marketing sends, payments, external commitments or scraping blocked/private sites.

## Evidence states

- `SOURCE_IMPORTED`: application source present, original release and license traceable, upstream Git history imported with workflow-path rewrite.
- `STATIC_BASELINE_PASS`: only version, license, Python compilation, upstream blocking Ruff rules and OpenAPI validation established by a successful Actions run.
- `RUNTIME_SMOKE_PASS`: only if install plus localhost HTTP startup genuinely pass on the fork's source; does not prove watch/reconciliation correctness, public deployment or HA.
- `VALUE_PROVEN`: real internal use validated against independent ground truth, with resource cost and known failure limits.
- `COMMERCIAL_PASS`: separate independent buyer willingness-to-pay evidence and Competitive Freshness Gate, not derived from GitHub stars or successful installation.

## Current scope

The existing single central Dots remains `OBSERVE`-only. This repo does not create another project manager, change existing Portfolio priorities, claim paid revenue, deploy a product or authorize paid infrastructure.
