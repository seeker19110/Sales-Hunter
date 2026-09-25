#!/usr/bin/env python3
"""Read-only Sales-Hunter audit probes. Never contacts any external platform.

Run against the reviewed checkout:
    PYTHONPATH=src python /path/to/audit_probes.py --output audit-results.json

These are observations, not a replacement test suite. A reproduced risk is NOT
reported as a passing quality check. All publishing uses a local recording fake.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable

from s_n_sales.pipeline.approval import ApprovalError, decide_approval
from s_n_sales.pipeline.publisher import Publisher, PublishError

REVIEWED_COMMIT = '0159c420ad8976939a98fb579bc9f5404bfcec89'
UTC = timezone.utc
NOW = datetime(2026, 9, 25, 3, 0, tzinfo=UTC)


def canonical_hash(candidate: dict[str, Any]) -> str:
    # Independent implementation of the canonical fields in publication.py.
    fields = ('affiliate_disclosure', 'affiliate_url', 'claim_snapshot',
              'content', 'observation_id')
    serialized = json.dumps({k: candidate[k] for k in fields}, ensure_ascii=False,
                            sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def candidate() -> dict[str, Any]:
    result = {
        'schema_version': 'publication-candidate.v1',
        'publication_id': 'audit-publication-001',
        'observation_id': 'audit-observation-001',
        'target_channel': 'local:audit-only',
        'content': 'Local synthetic deal: 80,000 VND.',
        'affiliate_url': 'https://example.com/affiliate/audit-only',
        'affiliate_disclosure': '#affiliate — Synthetic local audit example.',
        'claim_snapshot': {
            'platform': 'shopee', 'observed_at': '2026-09-25T02:59:00Z',
            'currency': 'VND', 'sale_price_minor': 80000,
            'list_price_minor': 100000,
            'source_url': 'https://example.com/product/audit-only',
        },
        'idempotency_key': 'audit-observation-001:local:audit-only:synthetic-key',
    }
    result['draft_sha256'] = canonical_hash(result)
    result['approval'] = {'status': 'pending', 'draft_sha256': result['draft_sha256']}
    return result


def approve(c: dict[str, Any]) -> dict[str, Any]:
    return decide_approval(c, status='approved', decided_by='local-auditor', decided_at=NOW)


class RecordingClient:
    """Local-only simulated provider, with no provider-side deduplication promise."""
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def publish_and_read_back(self, *, content: str, target_channel: str,
                              idempotency_key: str, now: datetime) -> dict[str, str]:
        self.calls.append({'content': content, 'target_channel': target_channel,
                           'idempotency_key': idempotency_key})
        post_id = f'local-post-{len(self.calls)}'
        return {
            'platform_post_id': post_id,
            'platform_post_url': f'https://example.com/local-only/{post_id}',
            'published_at': now.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }


def publisher(client: RecordingClient | None = None, **kwargs: Any) -> Publisher:
    return Publisher(client=client or RecordingClient(), dry_run=False, **kwargs)


results: list[dict[str, Any]] = []

def run_probe(identifier: str, description: str, probe: Callable[[], dict[str, Any]]) -> None:
    try:
        observations = probe()
        results.append({'id': identifier, 'description': description, **observations})
    except Exception as exc:
        results.append({'id': identifier, 'description': description,
                        'status': 'probe_error', 'error_type': type(exc).__name__,
                        'error': str(exc)})


def mutation_probe(field: str) -> dict[str, Any]:
    c = candidate()
    approval = approve(c)
    changed = deepcopy(c)
    if field == 'claim_snapshot':
        changed[field]['sale_price_minor'] = 1
    else:
        changed[field] += '-modified-after-approval'
    recalculated_hash_differs = canonical_hash(changed) != changed['draft_sha256']
    try:
        receipt = publisher().publish(changed, approval, now=NOW)
        return {'status': 'risk_reproduced', 'recalculated_hash_differs': recalculated_hash_differs,
                'receipt_status': receipt['status'],
                'expected_safe_behavior': 'Reject modified approved payload.'}
    except (ApprovalError, PublishError) as exc:
        return {'status': 'safety_control_observed', 'recalculated_hash_differs': recalculated_hash_differs,
                'error': str(exc)}


def minimal_approval() -> dict[str, Any]:
    c = candidate()
    incomplete = {'status': 'approved', 'publication_id': c['publication_id'],
                  'draft_sha256': c['draft_sha256']}
    try:
        receipt = publisher().publish(c, incomplete, now=NOW)
        return {'status': 'risk_reproduced', 'receipt_status': receipt['status'],
                'missing_fields_accepted': ['approval_id', 'decided_by', 'decided_at', 'schema_version']}
    except (ApprovalError, PublishError) as exc:
        return {'status': 'safety_control_observed', 'error': str(exc)}


def outgoing_payload() -> dict[str, Any]:
    c = candidate()
    client = RecordingClient()
    publisher(client).publish(c, approve(c), now=NOW)
    text = client.calls[0]['content']
    missing = [key for key in ('affiliate_url', 'affiliate_disclosure') if c[key] not in text]
    return {'status': 'risk_reproduced' if missing else 'safety_control_observed',
            'missing_from_outgoing_content': missing,
            'note': 'Fields exist in candidate metadata but are not composed into outgoing text.'}


def restart() -> dict[str, Any]:
    c = candidate()
    approval = approve(c)
    client = RecordingClient()
    first = publisher(client).publish(c, approval, now=NOW)
    second = publisher(client).publish(c, approval, now=NOW)
    return {'status': 'risk_reproduced' if len(client.calls) == 2 else 'safety_control_observed',
            'provider_call_count_after_new_publisher_instance': len(client.calls),
            'distinct_fake_remote_posts': first['platform_post_id'] != second['platform_post_id'],
            'limitation': 'Duplicate remote posts occur in this simulation because the fake provider '
                          'does not deduplicate. Real provider behavior has not been tested.'}


def stale_claim() -> dict[str, Any]:
    c = candidate()
    c['claim_snapshot']['observed_at'] = '2000-01-01T00:00:00Z'
    c['draft_sha256'] = canonical_hash(c)
    c['approval']['draft_sha256'] = c['draft_sha256']
    try:
        receipt = publisher().publish(c, approve(c), now=NOW)
        return {'status': 'risk_reproduced', 'observed_at': c['claim_snapshot']['observed_at'],
                'published_at': receipt['published_at'],
                'note': 'The publisher boundary itself applies no freshness policy.'}
    except (ApprovalError, PublishError) as exc:
        return {'status': 'safety_control_observed', 'error': str(exc)}


def utc_timestamp() -> dict[str, Any]:
    c = candidate()
    local_now = datetime(2026, 9, 25, 10, 0, tzinfo=timezone(timedelta(hours=7)))
    receipt = publisher().publish(c, approve(c), now=local_now)
    expected = local_now.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    return {'status': 'risk_reproduced' if receipt['read_back_at'] != expected else 'safety_control_observed',
            'input_time': local_now.isoformat(), 'actual_read_back_at': receipt['read_back_at'],
            'expected_read_back_at': expected,
            'fake_remote_published_at': receipt['published_at']}


def changed_hash_blocked() -> dict[str, Any]:
    c = candidate()
    approval = approve(c)
    c['draft_sha256'] = 'a' * 64
    try:
        publisher().publish(c, approval, now=NOW)
        return {'status': 'control_failed'}
    except ApprovalError:
        return {'status': 'safety_control_observed', 'blocked': True}


def dry_run_blocked() -> dict[str, Any]:
    c = candidate()
    client = RecordingClient()
    try:
        Publisher(client=client).publish(c, approve(c), now=NOW)
        return {'status': 'control_failed'}
    except PublishError:
        return {'status': 'safety_control_observed', 'blocked': True, 'provider_calls': len(client.calls)}


def kill_switch_blocked() -> dict[str, Any]:
    c = candidate()
    client = RecordingClient()
    try:
        publisher(client).publish(c, approve(c), now=NOW, system_kill_switch=True)
        return {'status': 'control_failed'}
    except PublishError:
        return {'status': 'safety_control_observed', 'blocked': True, 'provider_calls': len(client.calls)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('audit-results.json'))
    args = parser.parse_args()
    for field in ('content', 'affiliate_url', 'affiliate_disclosure', 'claim_snapshot'):
        run_probe(f'hash-tamper-{field}', f'Modify {field} without changing stored hash.',
                  lambda f=field: mutation_probe(f))
    run_probe('incomplete-approval', 'Publisher accepts an incomplete approval record.', minimal_approval)
    run_probe('outgoing-required-fields', 'Inspect final text passed to local fake.', outgoing_payload)
    run_probe('publisher-restart', 'Use the same candidate with two Publisher instances.', restart)
    run_probe('stale-observation', 'Publish boundary with an old observation.', stale_claim)
    run_probe('utc-conversion', 'Supply an aware Asia/Ho_Chi_Minh offset clock.', utc_timestamp)
    run_probe('control-changed-hash', 'Existing mismatched hash guard.', changed_hash_blocked)
    run_probe('control-dry-run', 'Existing default dry-run guard.', dry_run_blocked)
    run_probe('control-kill-switch', 'Existing explicit kill switch guard.', kill_switch_blocked)
    report = {
        'reviewed_commit': REVIEWED_COMMIT, 'audit_date': '2026-09-25',
        'scope': 'Isolated publisher/approval source modules, exact Git blob verified; synthetic '
                 'local-only provider. Not the full repository test suite or a production test.',
        'probe_count': len(results),
        'risk_reproduced_count': sum(r['status'] == 'risk_reproduced' for r in results),
        'safety_control_observed_count': sum(r['status'] == 'safety_control_observed' for r in results),
        'probe_error_count': sum(r['status'] == 'probe_error' for r in results),
        'results': results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
