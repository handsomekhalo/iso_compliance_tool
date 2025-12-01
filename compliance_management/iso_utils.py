import re
import hashlib
from typing import Tuple, List, Dict
from lxml import etree  # Make sure this is lxml, not xml.etree


def parse_iso20022_xml(xml_content: str) -> Tuple[int, int, List[Dict]]:
    """
    Parse ISO 20022 XML and find mismatches using lxml for full XPath support.

    Returns:
        (total_transactions, mismatches_count, mismatch_details)
    """
    try:
        # Remove XML comments
        xml_content = re.sub(r'<!--.*?-->', '', xml_content, flags=re.DOTALL)

        # Parse XML with lxml - ensure we're using lxml.etree
        root = etree.fromstring(xml_content.encode('utf-8'))

        transactions = []
        mismatches = []

        # Common ISO 20022 transaction elements
        transaction_tags = [
            'CdtTrfTxInf',      # pain.001 - Credit Transfer
            'DrctDbtTxInf',     # pain.008 - Direct Debit
            'TxInf',            # camt.053 - Bank Statement
            'Tx',               # Generic
            'PmtInf',           # Payment Information
        ]

        # Find all transactions using XPath with local-name()
        for tag in transaction_tags:
            transactions.extend(root.xpath(f'//*[local-name()="{tag}"]'))

        total_transactions = len(transactions)

        # If no transactions found, try broader search
        if total_transactions == 0:
            transactions = root.xpath('//*[contains(local-name(), "Tx") or contains(local-name(), "Pmt")]')
            total_transactions = len(transactions)

        # Validate each transaction
        for idx, txn in enumerate(transactions):
            issues = []

            # Check for Amount - use xpath() method, not find()
            amount_elem = txn.xpath('.//*[contains(local-name(), "Amt") or contains(local-name(), "Amount")]')
            has_amount = bool(amount_elem)

            # Check for Debtor
            debtor_elem = txn.xpath('.//*[contains(local-name(), "Dbtr") or contains(local-name(), "Debtor")]')
            has_debtor = bool(debtor_elem)

            # Check for Creditor
            creditor_elem = txn.xpath('.//*[contains(local-name(), "Cdtr") or contains(local-name(), "Creditor")]')
            has_creditor = bool(creditor_elem)

            if not has_amount:
                issues.append('Amount')
            if not has_debtor:
                issues.append('Debtor')
            if not has_creditor:
                issues.append('Creditor')

            if issues:
                # Safely extract values
                amount_value = None
                if has_amount and len(amount_elem) > 0:
                    # Handle both text content and attributes
                    amount_value = amount_elem[0].text or amount_elem[0].get('Ccy')
                
                debtor_name = None
                if has_debtor and len(debtor_elem) > 0:
                    name_nodes = debtor_elem[0].xpath('.//*[contains(local-name(), "Nm")]/text()')
                    debtor_name = name_nodes[0] if name_nodes else None
                
                creditor_name = None
                if has_creditor and len(creditor_elem) > 0:
                    name_nodes = creditor_elem[0].xpath('.//*[contains(local-name(), "Nm")]/text()')
                    creditor_name = name_nodes[0] if name_nodes else None

                mismatches.append({
                    'transaction_index': idx + 1,
                    'issue': 'Missing required fields',
                    'missing_fields': issues,
                    'details': {
                        'has_amount': has_amount,
                        'has_debtor': has_debtor,
                        'has_creditor': has_creditor,
                        'amount_value': amount_value,
                        'debtor_name': debtor_name,
                        'creditor_name': creditor_name
                    }
                })

        return total_transactions, len(mismatches), mismatches

    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing XML: {type(e).__name__} - {str(e)}")


def generate_xrpl_hash(content: str) -> str:
    """
    Generate SHA256 hash for XRPL audit trail
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def format_reconciliation_result(total: int, mismatches: int, details: List[Dict]) -> Dict:
    """
    Format reconciliation results for storage
    """
    accuracy = ((total - mismatches) / total * 100) if total > 0 else 0

    return {
        'summary': {
            'total_transactions': total,
            'successful': total - mismatches,
            'failed': mismatches,
            'accuracy_percentage': round(accuracy, 2)
        },
        'mismatches': details,
        'validation_rules_applied': [
            'Mandatory field presence check',
            'Amount field validation',
            'Debtor/Creditor information check'
        ]
    }