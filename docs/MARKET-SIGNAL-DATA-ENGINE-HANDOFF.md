# Market Signal Engine → Data Engine observation handoff (v1)

**Status (2026-10-10): PASS — inherited watch integration, producer schema serialization and independent Data Engine Go `extract.LoadBatch` consumer acceptance.** Not a live service-to-service connection, AI/semantic inference, or market truth.

## Existing target — no new analysis engine

Data Engine already defines `extract.Batch` and `model.Observation` in:
- [internal/extract/types.go](https://github.com/achirothmane/data-engine/blob/main/internal/extract/types.go)
- [internal/model/model.go](https://github.com/achirothmane/data-engine/blob/main/internal/model/model.go)

We therefore emit that **existing shape** directly, rather than invent a second acquisition/profiling/reconciliation runtime. [JSON Schema](contracts/data-engine-batch-v1.schema.json) constrains our emitted subset.

## Producer

`scripts/market_signal_handoff.py:make_snapshot_batch` takes two **already-pinned bytes** captured from the inherited watch-history API. It does not fetch URLs, interpret webpage HTML, infer price, choose trusted sources, access Dots, or send messages. It:

1. refuses missing identity, empty/equal snapshots, timezone-less observations, and redistribution without verified rights;
2. hashes both snapshot **bytes** (SHA-256);
3. uses separate revision-specific `entity_hint` identities rather than causing false same-instant conflicts between time-separated states;
4. labels raw `field=snapshot_sha256` evidence; it **does not assert numeric prices** or semantics;
5. produces the native `Batch` fields `job_id`, `kind`, `content_sha256`, `observations`, `warnings` with each `Observation` carrying source, times, license, redistribution flag, extraction method, and content hash.

**Timestamp boundary:** `observed_at` is when the handoff observed the snapshots, not a source-authored publication time. Snapshot history times and clocks require independent handling in a real deployment. `source_locator` marks `snapshot:baseline` vs `snapshot:changed`, and raw text/content remains upstream, not duplicated downstream by default.

## Integration experiment

The owned-fixture integration test:
- creates an actual watch using the inherited REST API;
- observes `USD 19.00` then `USD 23.00`;
- proves two snapshots and a meaningful diff;
- proves unchanged content does not create a third revision;
- maps exactly those two retrieved snapshot **byte strings** into the Data Engine Batch JSON and validates it against the local schema;
- uploads the redacted `mse-owned-page-evidence.json` and `mse-data-engine-batch.json` as private-to-run ephemeral GitHub Actions artifacts.

**Consumer evidence:** the exact data batch from [MSE Actions run 38089677370](https://github.com/achirothmane/market-signal-engine/actions/runs/38089677370) (artifact `11683373443`) was pinned in [Data Engine PR #22](https://github.com/achirothmane/data-engine/pull/22), which passed `go test ./...`, `go vet ./...` and its additional product CI, then merged as `8ca22b754364206175e474848af744304fc5bb5d`. The native `extract.LoadBatch` Go test verifies the decoded observations and pair hash. **Boundary:** this proves producer→artifact→native consumer interoperability, **not** automatic delivery, ongoing cross-service operation or extraction of prices from arbitrary sites.

## Rights, provenance and economic limits

Default `rights=unverified, redistribute=false`; changing that requires explicit source-level authorization. The only `redistribute=true` example is a synthetic **test-owned fixture**. Real-world watch HTML, personal data, model prompts, paid sources or credentials must never be exported to public GitHub artifacts.

No hosted service, customer payments, marketplace listing, agent authority or recurring infrastructure is introduced by this handoff.
