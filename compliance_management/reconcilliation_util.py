# reconciliation/utils.py

import csv
import json
import xml.etree.ElementTree as ET
import hashlib
from typing import Tuple, List, Dict, Any, Optional
import re
import hashlib
from lxml import etree

# Define maps at the module level to avoid re-instantiation

from django.core.exceptions import ValidationError
from io import BytesIO, StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile

from compliance_management.models import ISOFieldRule
from compliance_management.storage_util import delete_iso_xml_from_backblaze,upload_iso_xml_to_backblaze

# Import your Backblaze functions





# Define maps at the module level to avoid re-instantiation
MESSAGE_TRANSACTION_MAP = {
    "pacs.008": ["CdtTrfTxInf"],
    "pacs.009": ["CdtTrfTxInf"],
    "pain.001": ["CdtTrfTxInf"],
    "pain.008": ["DrctDbtTxInf"],
    "camt.053": ["Tx"],
}

def parse_iso20022_xml(xml_content: str, iso_profile: Any) -> Tuple[int, int, List[Dict]]:
    """
    Parses ISO 20022 XML against rules configured in an ISO profile.
    Optimised for low cyclomatic complexity.
    """
    try:
        # Sanitize and parse XML
        clean_xml = re.sub(r'<!--.*?-->', '', xml_content, flags=re.DOTALL)
        root = etree.fromstring(clean_xml.encode('utf-8'))

        # Determine tags to look for based on profile or auto-detection
        effective_type = _determine_effective_message_type(root, iso_profile.message_type)
        transaction_tags = MESSAGE_TRANSACTION_MAP.get(effective_type, ["Tx"])

        # Fetch all target transactions
        transactions = []
        for tag in transaction_tags:
            transactions.extend(root.xpath(f'//*[local-name()="{tag}"]'))

        # Fetch DB rules once outside the loop
        all_rules = ISOFieldRule.objects.filter(iso_profile=iso_profile)
        # Validate each transaction using specialized functions
        mismatches = []
        for idx, txn in enumerate(transactions):
            violations = _evaluate_transaction_rules(txn, all_rules)
            
            _evaluate_structured_remittance(txn, iso_profile, violations)

            if violations:
                mismatches.append({
                    "transaction_index": idx + 1,
                    "issue": "Profile rule violation",
                    "violations": violations
                })

        return len(transactions), len(mismatches), mismatches

    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing XML: {type(e).__name__} - {str(e)}")


def _determine_effective_message_type(root: etree._Element, profile_type: str) -> str:
    """Detects message type from root namespace and overrides profile if mismatched."""
    namespace = root.nsmap.get(None)
    if not namespace:
        return profile_type
    
    full_message_type = namespace.split(":")[-1]  # e.g., pain.001.001.03
    detected_type = ".".join(full_message_type.split(".")[:2])  # e.g., pain.001

    if detected_type != profile_type:
        print(f"[WARNING] Profile message_type '{profile_type}' "
              f"doesn't match XML '{detected_type}' — using XML type")
        return detected_type

    return profile_type


# def _evaluate_transaction_rules(txn: etree._Element, all_rules: list) -> List[str]:
#     """Iterates rules against a single transaction to isolate field-level complexity."""
#     violations = []
#     for rule in all_rules:
#         tag = rule.field_path.split("/")[-1].strip()
#         if not tag:
#             continue

#         elems = txn.xpath(f'.//*[local-name()="{tag}"]')
#         if not elems:
#             violations.append(rule.field_path)
            
#     return violations

def _resolve_field(txn: etree._Element, field_path: str):
    """
    Resolve a field_path against a transaction node.

    Supports:
      - nested paths: "CdtTrfTxInf/Amt/InstdAmt" or "Amt/InstdAmt"
      - single tag: "Cdtr"
      - fallback to last segment if full path fails

    Returns:
      (element_or_None, text_value)
    """
    if not field_path:
        return None, ""

    segments = [s.strip() for s in field_path.split("/") if s.strip()]
    if not segments:
        return None, ""

    def _text_of(elem):
        if elem is None:
            return ""
        # Direct text first
        value = (elem.text or "").strip()
        if value:
            return value
        # Fallback: first non-empty descendant text (handles container tags like <Amt>)
        texts = elem.xpath(".//text()")
        for t in texts:
            if t and t.strip():
                return t.strip()
        return ""

    # 1) Try walking the full path from the transaction node
    current = [txn]
    for seg in segments:
        next_nodes = []
        for node in current:
            next_nodes.extend(node.xpath(f'./*[local-name()="{seg}"]'))
            # also allow deeper search for this segment if direct child missing
            if not next_nodes:
                next_nodes.extend(node.xpath(f'.//*[local-name()="{seg}"]'))
        current = next_nodes
        if not current:
            break

    if current:
        elem = current[0]
        return elem, _text_of(elem)

    # 2) Fallback: last segment only (old behaviour)
    last = segments[-1]
    elems = txn.xpath(f'.//*[local-name()="{last}"]')
    if elems:
        return elems[0], _text_of(elems[0])

    return None, ""


def _evaluate_transaction_rules(txn: etree._Element, all_rules: list) -> List[str]:
    """
    Check every rule against one transaction.
    Uses nested field paths + max_length + regex.
    """
    violations = []

    for rule in all_rules:
        field_path = (rule.field_path or "").strip()
        if not field_path:
            continue

        elem, value = _resolve_field(txn, field_path)

        # 1. Presence
        if elem is None:
            violations.append(rule.field_path)
            continue

        # 2. max_length
        if rule.max_length is not None and len(value) > rule.max_length:
            violations.append(rule.field_path)
            continue

        # 3. regex
        if rule.regex:
            try:
                if not re.match(rule.regex, value):
                    violations.append(rule.field_path)
            except re.error:
                pass

    return violations

# def _evaluate_transaction_rules(txn: etree._Element, all_rules: list) -> List[str]:
#     """
#     Check every rule against one transaction.
#     Fails on: missing field, max_length exceeded, or regex mismatch.
#     """
#     violations = []

#     for rule in all_rules:
#         tag = rule.field_path.split("/")[-1].strip()
#         if not tag:
#             continue

#         elems = txn.xpath(f'.//*[local-name()="{tag}"]')

#         # 1. Presence
#         if not elems:
#             violations.append(rule.field_path)
#             continue

#         value = (elems[0].text or "").strip()

#         # 2. max_length
#         if rule.max_length is not None and len(value) > rule.max_length:
#             violations.append(rule.field_path)
#             continue

#         # 3. regex
#         if rule.regex:
#             try:
#                 if not re.match(rule.regex, value):
#                     violations.append(rule.field_path)
#             except re.error:
#                 # Invalid regex stored in DB — skip instead of crashing
#                 pass

#     return violations

def _evaluate_structured_remittance(txn, iso_profile, violations: list) -> None:
    if iso_profile.requires_structured_remittance:
        if not txn.xpath('.//*[local-name()="Strd"]'):
            violations.append("StructuredRemittanceRequired")

# def _evaluate_structured_remittance(txn: etree._Element, iso_profile: Any, violations: List[str]) -> None:
#     """Mutates violations list if mandatory structured remittance fields are absent."""
#     if not iso_profile.requires_structured_remittance:
#         return

#     if not txn.xpath('.//*[local-name()="Strd"]'):
#         violations.append("StructuredRemittanceRequired")



def upload_to_cloud_storage(file_content: bytes, filename: str, bank_id: int) -> Tuple[str, str, int]:
    """
    Upload file to Backblaze cloud storage
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        bank_id: Bank identifier
    
    Returns:
        (file_url, file_hash, file_size_bytes)
    """
    # Convert bytes to BytesIO for upload
    file_obj = BytesIO(file_content)
    file_obj.name = filename  # Set name attribute for upload
    
    # Upload to Backblaze
    file_url, file_hash, file_size = upload_iso_xml_to_backblaze(
        file_obj,
        bank_id,
        filename
    )
    
    if file_url is None:
        raise Exception("Failed to upload file to cloud storage")
    
    return file_url, file_hash, file_size


def delete_from_cloud_storage(file_url: str) -> bool:
    """
    Delete file from Backblaze cloud storage
    
    Args:
        file_url: URL of file to delete
    
    Returns:
        True if successful, False otherwise
    """
    return delete_iso_xml_from_backblaze(file_url)

def parse_iso20022_file(file_content: bytes, filename: str) -> Tuple[int, int, List[Dict]]:
    """
    Parse ISO 20022 file (XML, CSV, JSON, or Excel)
    
    Returns:
        (total_transactions, mismatches, mismatch_details)
    """
    file_extension = filename.lower().split('.')[-1]
    
    try:
        if file_extension == 'xml':
            return parse_iso20022_xml(file_content.decode('utf-8'))
        
        elif file_extension in ['xlsx', 'xls']:
            return parse_iso20022_excel(file_content)
        
        elif file_extension == 'csv':
            return parse_iso20022_csv(file_content.decode('utf-8'))
        
        elif file_extension == 'json':
            return parse_iso20022_json(file_content.decode('utf-8'))
        
        else:
            raise ValueError(f"Unsupported file format: .{file_extension}")
    
    except Exception as e:
        raise ValueError(f"Error parsing {file_extension.upper()}: {str(e)}")


def parse_iso20022_excel(file_content: bytes) -> Tuple[int, int, List[Dict]]:
    """Parse ISO 20022 Excel/XLSX format"""
    try:
        import openpyxl
        from io import BytesIO
        
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        sheet = workbook.active
        
        # Assume first row is headers
        headers = [cell.value for cell in sheet[1]]
        
        transactions = []
        mismatches = []
        
        # Read all rows (skip header)
        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=1):
            if any(row):  # Skip empty rows
                transaction = dict(zip(headers, row))
                transactions.append(transaction)
                
                # Validate required fields
                required_fields = ['Amount', 'Debtor', 'Creditor']
                missing_fields = [f for f in required_fields if not transaction.get(f)]
                
                if missing_fields:
                    mismatches.append({
                        'transaction_index': idx,
                        'issue': 'Missing required fields',
                        'details': {
                            'missing_fields': missing_fields
                        }
                    })
        
        return len(transactions), len(mismatches), mismatches
    
    except ImportError:
        raise ValueError("openpyxl library not installed. Run: pip install openpyxl")
    except Exception as e:
        raise ValueError(f"Excel parsing error: {str(e)}")


def parse_iso20022_csv(csv_content: str) -> Tuple[int, int, List[Dict]]:
    """Parse ISO 20022 CSV format"""
    try:
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        transactions = []
        mismatches = []
        
        for idx, row in enumerate(csv_reader, start=1):
            transactions.append(row)
            
            # Validate required fields
            required_fields = ['Amount', 'Debtor', 'Creditor']
            missing_fields = [f for f in required_fields if not row.get(f)]
            
            if missing_fields:
                mismatches.append({
                    'transaction_index': idx,
                    'issue': 'Missing required fields',
                    'details': {
                        'missing_fields': missing_fields
                    }
                })
        
        return len(transactions), len(mismatches), mismatches
    
    except Exception as e:
        raise ValueError(f"CSV parsing error: {str(e)}")


def parse_iso20022_json(json_content: str) -> Tuple[int, int, List[Dict]]:
    """Parse ISO 20022 JSON format"""
    try:
        data = json.loads(json_content)
        
        # Support different JSON structures
        if 'transactions' in data:
            transactions = data['transactions']
        elif 'payments' in data:
            transactions = data['payments']
        elif isinstance(data, list):
            transactions = data
        else:
            raise ValueError("Cannot find transactions in JSON structure")
        
        mismatches = []
        
        for idx, txn in enumerate(transactions, start=1):
            required_fields = ['amount', 'debtor', 'creditor']
            missing_fields = [f for f in required_fields if f not in txn]
            
            if missing_fields:
                mismatches.append({
                    'transaction_index': idx,
                    'issue': 'Missing required fields',
                    'details': {
                        'missing_fields': missing_fields
                    }
                })
        
        return len(transactions), len(mismatches), mismatches
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")


# Keep your existing helper functions
def generate_xrpl_hash(content: str) -> str:
    """Generate SHA256 hash for XRPL audit trail"""
    import hashlib
    if isinstance(content, bytes):
        return hashlib.sha256(content).hexdigest()
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


# def format_reconciliation_result(total: int, mismatches: int, details: List[Dict]) -> Dict:
#     """Format reconciliation results for storage"""
#     accuracy = ((total - mismatches) / total * 100) if total > 0 else 0
    
#     return {
#         'summary': {
#             'total_transactions': total,
#             'successful': total - mismatches,
#             'failed': mismatches,
#             'accuracy_percentage': round(accuracy, 2)
#         },
#         'mismatches': details,
#         'validation_rules_applied': [
#             'Mandatory field presence check',
#             'Amount field validation',
#             'Debtor/Creditor information check'
#         ]
#     }






# ─────────────────────────────────────────────────────────────────────────────
#
# It pulls rule names and weights dynamically from the DB
# instead of using hardcoded strings.
# ─────────────────────────────────────────────────────────────────────────────

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

    # for txn in transactions:
    #     txn_issues = []
    #     txn_score = 0
    #     rules_applied = []

    #     for rule in rules_list:
    #         # field = rule['field_name']
    #         field = rule['field_path']

    #         weight = rule.get('weight') or 0
    #         is_required = rule.get('is_required', False)
    #         field_value = txn.get(field)

    #         rule_result = {
    #             'field': field,
    #             'weight': weight,
    #             'required': is_required,
    #             'present': field_value not in (None, '', 'MISSING'),
    #             'passed': False,
    #         }

    #         if field_value and field_value != 'MISSING':
    #             rule_result['passed'] = True
    #             txn_score += weight
    #         else:
    #             if is_required:
    #                 issue = f"Required field '{field}' is missing or empty"
    #                 txn_issues.append(issue)
    #                 overall_issues.append(issue)

    #         rules_applied.append(rule_result)

    #     # Normalise score to 100
    #     normalised_score = round((txn_score / total_possible_weight) * 100) if total_possible_weight else 0

    #     scored_transactions.append({
    #         **txn,
    #         'compliance_score': normalised_score,
    #         'issues': txn_issues,
    #         'rules_applied': rules_applied,
    #     })

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


