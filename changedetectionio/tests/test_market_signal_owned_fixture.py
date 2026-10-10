"""Independent local-fixture evidence test for the inherited change detection engine.

This test exercises real inherited watch API and async workers. Its local fixture is
owned by the test; no outside website, paid provider or customer data is accessed.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone

from jsonschema import FormatChecker, validate
from scripts.market_signal_handoff import make_snapshot_batch

from flask import url_for

from .util import wait_for_all_checks, write_test_file_and_sync


FIRST = """<html><body><main>
<h1>Internal supply quote</h1>
<p>SKU MSE-OWNED-100 price USD 19.00 availability IN_STOCK</p>
</main></body></html>"""

SECOND = """<html><body><main>
<h1>Internal supply quote</h1>
<p>SKU MSE-OWNED-100 price USD 23.00 availability IN_STOCK</p>
</main></body></html>"""


def _api(client, path, api_key, **kwargs):
    response = client.get(path, headers={"x-api-key": api_key}, **kwargs)
    assert response.status_code == 200, (
        f"Expected GET {path} to succeed: {response.status_code}: "
        f"{response.get_data(as_text=True)[:500]}"
    )
    return response


def test_owned_page_change_history_and_negative_no_change(
    client, live_server, datastore_path
):
    """Initial snapshot -> actual change -> no-op: exactly two durable snapshots."""
    data = client.application.config["DATASTORE"]
    api_key = data.data["settings"]["application"]["api_access_token"]
    fixture_path = Path(datastore_path) / "endpoint-content.txt"
    source_url = url_for("test_endpoint", _external=True)

    write_test_file_and_sync(str(fixture_path), FIRST)
    create_response = client.post(
        url_for("createwatch"),
        data=json.dumps({"url": source_url, "title": "Owned market fixture"}),
        headers={"content-type": "application/json", "x-api-key": api_key},
    )
    assert create_response.status_code == 201, create_response.get_data(as_text=True)
    watch_uuid = create_response.get_json()["uuid"]

    # The inherited worker performs actual HTTP requests to the local fixture.
    wait_for_all_checks(client)
    initial = _api(client, url_for("watchhistory", uuid=watch_uuid), api_key).get_json()
    assert len(initial) == 1, f"Expected exactly one baseline snapshot, got {initial}"

    initial_body = _api(
        client, url_for("watchsinglehistory", uuid=watch_uuid, timestamp="latest"),
        api_key
    ).data
    assert b"USD 19.00" in initial_body
    assert data.data["watching"][watch_uuid].get("last_error") in (False, None, "")

    # Give timestamp bookkeeping a distinct clock second (as upstream tests do).
    time.sleep(2)
    write_test_file_and_sync(str(fixture_path), SECOND)
    recheck = _api(
        client, url_for("createwatch", recheck_all="1"), api_key
    )
    wait_for_all_checks(client)

    changed_history = _api(
        client, url_for("watchhistory", uuid=watch_uuid), api_key
    ).get_json()
    assert len(changed_history) == 2, (
        f"Expected changed snapshot, got {changed_history}"
    )
    changed_body = _api(
        client, url_for("watchsinglehistory", uuid=watch_uuid, timestamp="latest"),
        api_key
    ).data
    assert b"USD 23.00" in changed_body and b"USD 19.00" not in changed_body

    actual_diff = _api(
        client,
        url_for(
            "watchhistorydiff",
            uuid=watch_uuid,
            from_timestamp="previous",
            to_timestamp="latest"
        ),
        api_key
    ).data
    assert b"23.00" in actual_diff, actual_diff[:1000]
    assert b"19.00" in actual_diff, actual_diff[:1000]

    # A fresh check on byte-identical content MUST NOT produce a third revision.
    time.sleep(2)
    _api(client, url_for("createwatch", recheck_all="1"), api_key)
    wait_for_all_checks(client)
    unchanged_history = _api(
        client, url_for("watchhistory", uuid=watch_uuid), api_key
    ).get_json()
    assert len(unchanged_history) == 2, (
        f"False positive: identical fixture produced history {unchanged_history}"
    )
    assert set(unchanged_history) == set(changed_history)
    assert data.data["watching"][watch_uuid].get("last_error") in (False, None, "")

    # Evidence only includes test-owned bytes, digests, and proven assertions.
    # Never persist API credentials, private sites, or customer content here.
    evidence = {
        "schema_version": 1,
        "experiment": "local_owned_html_watch",
        "source_kind": "owned_ephemeral_local_fixture",
        "watch_identity": "redacted",
        "stage_count": 3,
        "snapshots_after_initial": len(initial),
        "snapshots_after_change": len(changed_history),
        "snapshots_after_identical_recheck": len(unchanged_history),
        "initial_snapshot_sha256": hashlib.sha256(initial_body).hexdigest(),
        "changed_snapshot_sha256": hashlib.sha256(changed_body).hexdigest(),
        "change_diff_sha256": hashlib.sha256(actual_diff).hexdigest(),
        "changed_snapshot_distinct": initial_body != changed_body,
        "price_change_verified": True,
        "identical_recheck_no_new_history": True,
        "inherited_worker_and_api": True,
        "claim_boundaries": [
            "not a real third-party website",
            "not an external paid market feed",
            "no notification delivery asserted",
            "not a multi-day production soak",
            "no cross-system Data Engine integration asserted"
        ]
    }
    batch = make_snapshot_batch(
        source_id="owned-mse-fixture-100",
        source_ref="owned-fixture:market-signal-ci",
        baseline=initial_body,
        changed=changed_body,
        observed_at=datetime.now(timezone.utc),
        rights="owned-ci-fixture",
        redistribute=True,
    )
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "docs/contracts/data-engine-batch-v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(instance=batch, schema=schema, format_checker=FormatChecker())
    assert [o["raw_value"] for o in batch["observations"]] == [
        evidence["initial_snapshot_sha256"],
        evidence["changed_snapshot_sha256"],
    ]
    assert all(o["redistribute"] for o in batch["observations"])
    assert batch["observations"][0]["entity_hint"] != batch["observations"][1]["entity_hint"]
    batch_path = os.getenv("MSE_BATCH_PATH")
    if batch_path:
        output = Path(batch_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n")
    print("DATA_ENGINE_BATCH_SERIALIZATION_CONTRACT: PASS")

    evidence_path = os.getenv("MSE_EVIDENCE_PATH")
    if evidence_path:
        output = Path(evidence_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print("OWNED_PAGE_CHANGE_EVIDENCE: PASS", json.dumps({
        "snapshots": [len(initial), len(changed_history), len(unchanged_history)],
        "no_false_positive": True,
        "actual_diff_sha256": evidence["change_diff_sha256"],
    }))
