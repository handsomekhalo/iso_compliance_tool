import re
import hashlib
from typing import Tuple, List, Dict
from lxml import etree  # Make sure this is lxml, not xml.etree



def generate_xrpl_hash(content: str) -> str:
    """
    Generate SHA256 hash for XRPL audit trail
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def format_reconciliation_result(parsed_data, iso_profile=None):
    """
    Takes the output of parse_iso20022_xml and formats it into the
    result_json structure stored on ISOReconciliationLog.

    Rules and their weights are pulled dynamically from ISOFieldRule
    records attached to the iso_profile — no hardcoded strings.
    """
    from compliance_management.models import ISOFieldRule  # local import avoids circular

    # ── Load rules from DB ─────────────────────────────────────────────────
    if iso_profile:
        db_rules = ISOFieldRule.objects.filter(
            iso_profile=iso_profile
        ).values('field_path', 'required', 'weight')

        rules_list = list(db_rules)
    else:
        rules_list = []

    total_possible_weight = sum(r['weight'] for r in rules_list if r.get('weight')) or 100

    # ── Score each transaction against the rules ───────────────────────────
    transactions = parsed_data.get('transactions', [])
    scored_transactions = []
    overall_issues = []

    for txn in transactions:
        txn_issues = []
        txn_score = 0
        rules_applied = []

        # ── Normalise parser output shape ──────────────────────────────────
        # Parser returns violations as a list of failed field paths.
        # Convert to a set for O(1) lookup.
        violations = set(txn.get('violations', []))

        for rule in rules_list:
            field = rule['field_path']
            weight = rule.get('weight') or 0
            is_required = rule.get('required', False)

            # Field passed if it's NOT in the violations list
            passed = field not in violations

            rule_result = {
                'field':    field,
                'weight':   weight,
                'required': is_required,
                'passed':   passed,
            }

            if passed:
                txn_score += weight
            else:
                if is_required:
                    issue = f"Required field '{field}' failed validation"
                    txn_issues.append(issue)

            rules_applied.append(rule_result)

        normalised_score = round((txn_score / total_possible_weight) * 100) if total_possible_weight else 0

        scored_transactions.append({
            'transaction_index': txn.get('transaction_index'),
            'compliance_score':  normalised_score,
            'issues':            txn_issues,
            'rules_applied':     rules_applied,
            'original_issue':    txn.get('issue', ''),
        })
    # ── Summary ────────────────────────────────────────────────────────────
    scores = [t['compliance_score'] for t in scored_transactions]
    avg_score = round(sum(scores) / len(scores)) if scores else 0
    passed = sum(1 for s in scores if s >= 80)
    failed = len(scores) - passed

    result = {
        'summary': {
            'total_transactions': len(scored_transactions),
            'passed': passed,
            'failed': failed,
            'average_score': avg_score,
            'total_possible_weight': total_possible_weight,
            'rules_evaluated': len(rules_list),
            'profile_name': iso_profile.name if iso_profile else None,
        },
        'transactions': scored_transactions,
        'issues': list(set(overall_issues)),  # deduplicated
        # 'validation_rules_applied': [r['field_name'] for r in rules_list],
        'validation_rules_applied': [r['field_path'] for r in rules_list],

    }

    return result
