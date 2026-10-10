"""Pure, evidence-only adapter to Data Engine's existing extract.Batch wire shape.

Does not fetch a URL, infer a value, access a database, or trigger AI/action.
The consumer is Data Engine's internal/extract/types.go / internal/model/model.go.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256


def _hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def make_snapshot_batch(
    *,
    source_id: str,
    source_ref: str,
    baseline: bytes,
    changed: bytes,
    observed_at: datetime,
    rights: str = "unverified",
    redistribute: bool = False,
) -> dict:
    """Emit two *revision-specific* raw observations, never assert semantic truth.

    Default rights are intentionally restrictive; no automatic data resale.
    Two revisions have different entity hints so downstream reconciliation
    does not mistake time progression for same-instant source disagreement.
    """
    if not source_id or not source_ref:
        raise ValueError("source identity and source ref required")
    if not baseline or not changed or baseline == changed:
        raise ValueError("two different non-empty pinned snapshots are required")
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    if not rights:
        raise ValueError("explicit rights decision required")
    if redistribute and rights == "unverified":
        raise ValueError("cannot assert redistribution without verified rights")

    iso = observed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    first_hash = _hex(baseline)
    second_hash = _hex(changed)
    pair_hash = _hex((first_hash + "\n" + second_hash).encode("ascii"))

    def observation(revision: str, content_hash: str) -> dict:
        # exact field names match github.com/achirothmane/data-engine:
        # extract.Batch.observations[]model.Observation
        return {
            "entity_hint": f"{source_id}:{revision}:{content_hash[:12]}",
            "field": "snapshot_sha256",
            "raw_value": content_hash,
            "source_id": source_id,
            "source_ref": source_ref,
            "source_locator": f"snapshot:{revision}",
            "observed_at": iso,
            "retrieved_at": iso,
            "license": rights,
            "redistribute": redistribute,
            "extraction_method": "market-signal:versioned-snapshot-hash",
            "content_sha256": content_hash,
        }

    return {
        "job_id": f"mse-snapshot-pair-{pair_hash[:24]}",
        "kind": "market_signal_snapshots",
        "content_sha256": pair_hash,
        "observations": [
            observation("baseline", first_hash),
            observation("changed", second_hash),
        ],
        "warnings": [
            "Change proven only against provided byte snapshots; semantic values not inferred.",
            "Observed_at is handoff observation time, not publication time.",
            "No external Data Engine runtime invocation is implied."
        ],
    }
