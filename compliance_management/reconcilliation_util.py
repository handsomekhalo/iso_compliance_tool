# reconciliation/utils.py

import csv
import json
import xml.etree.ElementTree as ET
import hashlib
from typing import Dict, List, Tuple
from io import BytesIO, StringIO
from django.core.files.uploadedfile import InMemoryUploadedFile

from compliance_management.storage_util import delete_iso_xml_from_backblaze, upload_iso_xml_to_backblaze

# Import your Backblaze functions



import re
import hashlib
from typing import Tuple, List, Dict
from lxml import etree

# def parse_iso20022_xml(xml_content: str) -> Tuple[int, int, List[Dict]]:
#     """
#     Parse ISO 20022 XML and find mismatches using lxml for full XPath support.

#     Returns:
#         (total_transactions, mismatches_count, mismatch_details)
#     """
#     try:
#         # Remove XML comments
#         xml_content = re.sub(r'<!--.*?-->', '', xml_content, flags=re.DOTALL)

#         # Parse XML with lxml
#         root = etree.fromstring(xml_content.encode('utf-8'))

#         transactions = []
#         mismatches = []

#         # Common ISO 20022 transaction elements
#         transaction_tags = [
#             'CdtTrfTxInf',      # pain.001 - Credit Transfer
#             'DrctDbtTxInf',     # pain.008 - Direct Debit
#             'TxInf',            # camt.053 - Bank Statement
#             'Tx',               # Generic
#             'PmtInf',           # Payment Information
#         ]

#         # Find all transactions using XPath with local-name()
#         for tag in transaction_tags:
#             transactions.extend(root.xpath(f'//*[local-name()="{tag}"]'))

#         total_transactions = len(transactions)

#         # If no transactions found, try broader search
#         if total_transactions == 0:
#             transactions = root.xpath('//*[contains(local-name(), "Tx") or contains(local-name(), "Pmt")]')
#             total_transactions = len(transactions)

#         # Validate each transaction
#         for idx, txn in enumerate(transactions):
#             issues = []

#             # Check for Amount
#             amount_elem = txn.xpath('.//*[contains(local-name(), "Amt") or contains(local-name(), "Amount")]')
#             has_amount = bool(amount_elem)

#             # Check for Debtor
#             debtor_elem = txn.xpath('.//*[contains(local-name(), "Dbtr") or contains(local-name(), "Debtor")]')
#             has_debtor = bool(debtor_elem)

#             # Check for Creditor
#             creditor_elem = txn.xpath('.//*[contains(local-name(), "Cdtr") or contains(local-name(), "Creditor")]')
#             has_creditor = bool(creditor_elem)

#             if not has_amount:
#                 issues.append('Amount')
#             if not has_debtor:
#                 issues.append('Debtor')
#             if not has_creditor:
#                 issues.append('Creditor')

#             if issues:
#                 mismatches.append({
#                     'transaction_index': idx + 1,
#                     'issue': 'Missing required fields',
#                     'missing_fields': issues,
#                     'details': {
#                         'has_amount': has_amount,
#                         'has_debtor': has_debtor,
#                         'has_creditor': has_creditor,
#                         'amount_value': amount_elem[0].text if has_amount else None,
#                         'debtor_name': debtor_elem[0].xpath('.//*[contains(local-name(), "Nm")]/text()')[0]
#                                        if has_debtor and debtor_elem[0].xpath('.//*[contains(local-name(), "Nm")]/text()')
#                                        else None,
#                         'creditor_name': creditor_elem[0].xpath('.//*[contains(local-name(), "Nm")]/text()')[0]
#                                          if has_creditor and creditor_elem[0].xpath('.//*[contains(local-name(), "Nm")]/text()')
#                                          else None
#                     }
#                 })

#         return total_transactions, len(mismatches), mismatches

#     except etree.XMLSyntaxError as e:
#         raise ValueError(f"Invalid XML format: {str(e)}")
#     except Exception as e:
#         raise ValueError(f"Error parsing XML: {type(e).__name__} - {str(e)}")

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


# def parse_iso20022_xml(xml_content: str) -> Tuple[int, int, List[Dict]]:
#     """Parse ISO 20022 XML format (your existing function)"""
#     try:
#         root = ET.fromstring(xml_content)
        
#         transactions = []
#         mismatches = []
        
#         # Common ISO 20022 transaction elements
#         transaction_tags = [
#             'CdtTrfTxInf',      # pain.001 - Credit Transfer
#             'DrctDbtTxInf',     # pain.008 - Direct Debit
#             'TxInf',            # camt.053 - Bank Statement
#             'Tx',               # Generic
#             'PmtInf',           # Payment Information
#         ]
        
#         for tag in transaction_tags:
#             for elem in root.iter():
#                 if elem.tag.endswith(tag):
#                     transactions.append(elem)
        
#         total_transactions = len(transactions)
        
#         # If no transactions found, try counting payment entries differently
#         if total_transactions == 0:
#             # Look for any element with "Tx" or "Pmt" in tag name
#             for elem in root.iter():
#                 if 'Tx' in elem.tag or 'Pmt' in elem.tag:
#                     transactions.append(elem)
#             total_transactions = len(transactions)
        
#         # Validate transactions
#         for idx, txn in enumerate(transactions):
#             has_amount = txn.find('.//*[contains(local-name(), "Amt")]') is not None
#             has_debtor = txn.find('.//*[contains(local-name(), "Dbtr")]') is not None
#             has_creditor = txn.find('.//*[contains(local-name(), "Cdtr")]') is not None
            
#             if not (has_amount and has_debtor and has_creditor):
#                 mismatches.append({
#                     'transaction_index': idx + 1,
#                     'issue': 'Missing required fields',
#                     'details': {
#                         'has_amount': has_amount,
#                         'has_debtor': has_debtor,
#                         'has_creditor': has_creditor
#                     }
#                 })
        
#         return total_transactions, len(mismatches), mismatches
    
#     except ET.ParseError as e:
#         raise ValueError(f"Invalid XML format: {str(e)}")


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


def format_reconciliation_result(total: int, mismatches: int, details: List[Dict]) -> Dict:
    """Format reconciliation results for storage"""
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