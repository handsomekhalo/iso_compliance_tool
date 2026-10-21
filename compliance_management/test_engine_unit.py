"""
Unit tests for the ISO scoring engine helpers (Steps 1–4).
No cloud upload, minimal DB — fast and targeted.
"""
import pytest
from lxml import etree

from compliance_management.models import ISOProfile, ISOFieldRule
from compliance_management.reconcilliation_util import (
    parse_iso20022_xml,
    generate_xrpl_hash,
    format_reconciliation_result,
    _evaluate_basic_content_checks,
    _resolve_field,
)


# Minimal pain.001-style transaction fragment wrapped as a full doc
GOOD_PAIN001 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr><MsgId>MSG-1</MsgId><NbOfTxs>1</NbOfTxs></GrpHdr>
    <PmtInf>
      <PmtInfId>PMT-1</PmtInfId>
      <CdtTrfTxInf>
        <PmtId>
          <InstrId>INSTR-1</InstrId>
          <EndToEndId>E2E-1</EndToEndId>
        </PmtId>
        <Amt><InstdAmt Ccy="EUR">1250.75</InstdAmt></Amt>
        <Cdtr><Nm>Example GmbH</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>DE89370400440532013000</IBAN></Id></CdtrAcct>
        <CdtrAgt><FinInstnId><BIC>DEUTDEFFXXX</BIC></FinInstnId></CdtrAgt>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>
"""

BAD_AMOUNT_PAIN001 = GOOD_PAIN001.replace("1250.75", "abc")


@pytest.fixture
def profile_with_amt_rule(db):
    profile = ISOProfile.objects.create(
        name="Unit Test Profile",
        message_type="pain.001",
        version="001.03",
        is_default=False,
        is_active=True,
    )
    ISOFieldRule.objects.create(
        iso_profile=profile,
        field_path="CdtTrfTxInf/Amt",
        required=True,
        weight=35,
        max_length=None,
        regex="",
    )
    return profile


@pytest.mark.django_db
class TestParseAndContentChecks:

    def test_good_file_finds_one_transaction(self, profile_with_amt_rule):
        total, mismatches, details = parse_iso20022_xml(GOOD_PAIN001, profile_with_amt_rule)
        assert total == 1
        # Amt present + numeric → should not fail content:amount_*
        if details:
            assert "content:amount_not_numeric" not in details[0].get("violations", [])
            assert "content:amount_missing" not in details[0].get("violations", [])

    def test_bad_amount_adds_content_violation(self, profile_with_amt_rule):
        total, mismatches, details = parse_iso20022_xml(BAD_AMOUNT_PAIN001, profile_with_amt_rule)
        assert total == 1
        assert mismatches >= 1
        violations = details[0]["violations"]
        assert "content:amount_not_numeric" in violations

    def test_max_length_fails_when_value_too_long(self, profile_with_amt_rule):
        rule = ISOFieldRule.objects.get(iso_profile=profile_with_amt_rule, field_path="CdtTrfTxInf/Amt")
        rule.max_length = 2
        rule.save()

        total, mismatches, details = parse_iso20022_xml(GOOD_PAIN001, profile_with_amt_rule)
        assert mismatches >= 1
        assert "CdtTrfTxInf/Amt" in details[0]["violations"]

    def test_regex_pass_and_fail(self, profile_with_amt_rule):
        rule = ISOFieldRule.objects.get(iso_profile=profile_with_amt_rule, field_path="CdtTrfTxInf/Amt")
        rule.regex = r"^[0-9.]+$"
        rule.save()

        _, _, good = parse_iso20022_xml(GOOD_PAIN001, profile_with_amt_rule)
        good_violations = good[0]["violations"] if good else []
        assert "CdtTrfTxInf/Amt" not in good_violations

        rule.regex = r"^FAIL$"
        rule.save()
        _, mismatches, bad = parse_iso20022_xml(GOOD_PAIN001, profile_with_amt_rule)
        assert mismatches >= 1
        assert "CdtTrfTxInf/Amt" in bad[0]["violations"]


class TestResolveFieldAndHash:
    """No DB required."""

    def test_resolve_nested_amt_reads_instd_amt_text(self):
        root = etree.fromstring(GOOD_PAIN001.encode("utf-8"))
        txn = root.xpath('//*[local-name()="CdtTrfTxInf"]')[0]
        elem, value = _resolve_field(txn, "CdtTrfTxInf/Amt")
        # path may resolve via last segment / nested walk
        assert value == "1250.75" or (elem is not None and "1250" in value)

    def test_resolve_amt_instd_amt_path(self):
        root = etree.fromstring(GOOD_PAIN001.encode("utf-8"))
        txn = root.xpath('//*[local-name()="CdtTrfTxInf"]')[0]
        elem, value = _resolve_field(txn, "Amt/InstdAmt")
        assert elem is not None
        assert value == "1250.75"

    def test_generate_xrpl_hash_stable(self):
        h1 = generate_xrpl_hash("hello")
        h2 = generate_xrpl_hash("hello")
        h3 = generate_xrpl_hash(b"hello")
        assert h1 == h2 == h3
        assert len(h1) == 64


@pytest.mark.django_db
class TestFormatResultExposesViolations:

    def test_violations_included_in_output(self, profile_with_amt_rule):
        parsed = {
            "transactions": [
                {
                    "transaction_index": 1,
                    "issue": "Profile rule violation",
                    "violations": ["CdtTrfTxInf/Amt", "content:amount_not_numeric"],
                }
            ]
        }
        result = format_reconciliation_result(parsed, iso_profile=profile_with_amt_rule)
        txn = result["transactions"][0]
        assert "violations" in txn
        assert "content:amount_not_numeric" in txn["violations"]
        assert txn["compliance_score"] < 100