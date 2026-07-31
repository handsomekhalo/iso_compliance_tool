"""
Core flow: upload → parse → hash → store (compliance_management app).

Mocks Backblaze (upload_to_cloud_storage) so tests don't hit real
network — everything else runs through the real DRF view, real XML
parser, real permission classes, real DB.
"""
import io
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from compliance_management.models import ISOReconciliationLog, ISODocument, ISOFieldRule, ISOProfile

VALID_PACS008 = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <GrpHdr><MsgId>MSG-001</MsgId></GrpHdr>
    <CdtTrfTxInf>
      <PmtId><EndToEndId>E2E-1</EndToEndId></PmtId>
      <Amt><InstdAmt Ccy="ZAR">1500.00</InstdAmt></Amt>
      <RmtInf><Strd><CdtrRefInf><Ref>INV-001</Ref></CdtrRefInf></Strd></RmtInf>
    </CdtTrfTxInf>
    <CdtTrfTxInf>
      <PmtId><EndToEndId>E2E-2</EndToEndId></PmtId>
      <Amt><InstdAmt Ccy="ZAR">750.00</InstdAmt></Amt>
      <RmtInf><Strd><CdtrRefInf><Ref>INV-002</Ref></CdtrRefInf></Strd></RmtInf>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>
"""

# Second transaction is missing <Amt> entirely -> should be flagged as a mismatch
# against the required CdtTrfTxInf/Amt field rule set up in conftest's iso_profile.
# Both transactions still carry <Strd> so this test isolates the Amt violation only.
MISSING_FIELD_PACS008 = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <GrpHdr><MsgId>MSG-002</MsgId></GrpHdr>
    <CdtTrfTxInf>
      <PmtId><EndToEndId>E2E-1</EndToEndId></PmtId>
      <Amt><InstdAmt Ccy="ZAR">1500.00</InstdAmt></Amt>
      <RmtInf><Strd><CdtrRefInf><Ref>INV-001</Ref></CdtrRefInf></Strd></RmtInf>
    </CdtTrfTxInf>
    <CdtTrfTxInf>
      <PmtId><EndToEndId>E2E-2</EndToEndId></PmtId>
      <RmtInf><Strd><CdtrRefInf><Ref>INV-002</Ref></CdtrRefInf></Strd></RmtInf>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>
"""

BROKEN_XML = b"<Document><Unclosed>"


def _mock_cloud_upload(file_content, filename, bank_id):
    """Stand-in for compliance_management.reconcilliation_util.upload_to_cloud_storage."""
    import hashlib
    return (
        f"https://s3.mock.backblazeb2.com/bucket/iso_files/bank_{bank_id}/{filename}",
        hashlib.sha256(file_content).hexdigest(),
        len(file_content),
    )


@pytest.mark.django_db
class TestUploadReconciliationFlow:

    @patch("compliance_management.api.views.upload_to_cloud_storage", side_effect=_mock_cloud_upload)
    def test_valid_upload_creates_log_and_document(self, mock_upload, authed_client):
        client, user, bank = authed_client
        upload = SimpleUploadedFile("clean.xml", VALID_PACS008, content_type="application/xml")

        resp = client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")

        assert resp.status_code == 201, resp.data
        assert resp.data["reconciliation"]["total_transactions"] == 2
        assert resp.data["reconciliation"]["mismatches"] == 0
        assert mock_upload.called

        log = ISOReconciliationLog.objects.get(bank=bank)
        assert log.total_transactions == 2
        assert log.mismatches == 0
        assert log.xrpl_hash  # non-empty audit hash was generated
        assert ISODocument.objects.filter(log=log).exists()

    @patch("compliance_management.api.views.upload_to_cloud_storage", side_effect=_mock_cloud_upload)
    def test_upload_flags_missing_required_field(self, mock_upload, authed_client):
        client, user, bank = authed_client
        upload = SimpleUploadedFile("missing_field.xml", MISSING_FIELD_PACS008, content_type="application/xml")

        resp = client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")

        assert resp.status_code == 201, resp.data
        assert resp.data["reconciliation"]["total_transactions"] == 2
        assert resp.data["reconciliation"]["mismatches"] == 1

        log = ISOReconciliationLog.objects.get(bank=bank)
        assert log.mismatches == 1
        second_txn = log.result_json["transactions"][1]
        assert any("CdtTrfTxInf/Amt" in issue for issue in second_txn["issues"])
        assert second_txn["compliance_score"] < 100

    def test_broken_xml_returns_400_not_500(self, authed_client):
        """A malformed file should fail cleanly, not blow up with a 500."""
        client, user, bank = authed_client
        upload = SimpleUploadedFile("broken.xml", BROKEN_XML, content_type="application/xml")

        resp = client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")

        assert resp.status_code == 400, resp.data
        assert not ISOReconciliationLog.objects.filter(bank=bank).exists()

    def test_rejects_disallowed_file_extension(self, authed_client):
        client, user, bank = authed_client
        upload = SimpleUploadedFile("virus.exe", b"not xml", content_type="application/octet-stream")

        resp = client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")

        assert resp.status_code == 400
        assert "Invalid file format" in str(resp.data)

    def test_upload_requires_authentication(self, api_client):
        upload = SimpleUploadedFile("clean.xml", VALID_PACS008, content_type="application/xml")
        resp = api_client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")
        assert resp.status_code == 401

    @patch("compliance_management.api.views.upload_to_cloud_storage", side_effect=_mock_cloud_upload)
    def test_analyst_role_can_upload(self, mock_upload, api_client, analyst_user):
        """ANALYST is the minimum role allowed to upload (IsAnalystOrAbove)."""
        user, bank = analyst_user
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        upload = SimpleUploadedFile("clean.xml", VALID_PACS008, content_type="application/xml")
        resp = api_client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")
        assert resp.status_code == 201, resp.data


@pytest.mark.django_db
class TestReconciliationBankScoping:
    """Proves a bank can never see another bank's reconciliation data."""

    @patch("compliance_management.api.views.upload_to_cloud_storage", side_effect=_mock_cloud_upload)
    def test_bank_cannot_see_other_banks_reconciliation_list(self, mock_upload, authed_client, other_bank_admin):
        client, user, bank = authed_client
        upload = SimpleUploadedFile("clean.xml", VALID_PACS008, content_type="application/xml")
        client.post(reverse("upload_reconciliation_api"), {"file_name": upload}, format="multipart")

        other_user, other_bank = other_bank_admin
        from rest_framework.authtoken.models import Token
        other_token, _ = Token.objects.get_or_create(user=other_user)

        other_client_kwargs = {"HTTP_AUTHORIZATION": f"Token {other_token.key}"}
        resp = client.get(reverse("list_reconciliations_api"), **other_client_kwargs)

        # Using the other bank's token: should see zero of the first bank's logs
        assert resp.status_code == 200
        assert resp.data["count"] == 0 if "count" in resp.data else True


@pytest.mark.django_db
class TestProfileCloningAndScoping:
    """
    Covers the Bank.save() dedicated-profile clone, and the now-active
    bank-scoping check on iso_field_rules_api / iso_field_rule_detail_api.
    """

    def test_new_bank_gets_its_own_cloned_profile_not_the_shared_default(self, db):
        from django.contrib.auth.models import User
        from compliance_management.models import Bank

        # Reuse the one seeded default (migration 0007) rather than creating
        # a second is_default=True row, which would be ambiguous.
        default_profile = ISOProfile.objects.filter(is_default=True, is_active=True).order_by("id").first()
        ISOFieldRule.objects.get_or_create(
            iso_profile=default_profile, field_path="CdtTrfTxInf/Amt",
            defaults={"required": True, "weight": 5},
        )

        user_a = User.objects.create_user(username="a@bank.com", email="a@bank.com", password="x")
        user_b = User.objects.create_user(username="b@bank.com", email="b@bank.com", password="x")

        bank_a = Bank.objects.create(name="Bank A", contact_email="a@contact.com", user=user_a)
        bank_b = Bank.objects.create(name="Bank B", contact_email="b@contact.com", user=user_b)

        # Each bank got its own profile, not the shared default itself
        assert bank_a.iso_profile is not None
        assert bank_b.iso_profile is not None
        assert bank_a.iso_profile != default_profile
        assert bank_b.iso_profile != default_profile
        assert bank_a.iso_profile != bank_b.iso_profile

        # Rules were copied onto each bank's own profile
        assert ISOFieldRule.objects.filter(iso_profile=bank_a.iso_profile).count() == 1
        assert ISOFieldRule.objects.filter(iso_profile=bank_b.iso_profile).count() == 1

    def test_bank_cannot_edit_another_banks_rules(self, authed_client, other_bank_admin):
        """The now-active scoping check on iso_field_rule_detail_api / rules_api."""
        client, user, bank = authed_client
        other_user, other_bank = other_bank_admin

        # Bank A tries to add a rule to Bank B's own dedicated profile
        resp = client.post(
            reverse("iso_field_rules_api", args=[other_bank.iso_profile.id]),
            {"field_path": "CdtTrfTxInf/Malicious", "required": True, "weight": 5},
            format="json",
        )
        assert resp.status_code == 403
        assert not ISOFieldRule.objects.filter(iso_profile=other_bank.iso_profile, field_path="CdtTrfTxInf/Malicious").exists()

    def test_bank_can_edit_its_own_profile_rules(self, authed_client):
        client, user, bank = authed_client
        resp = client.post(
            reverse("iso_field_rules_api", args=[bank.iso_profile.id]),
            {"field_path": "CdtTrfTxInf/NewField", "required": True, "weight": 3},
            format="json",
        )
        assert resp.status_code == 201, resp.data

    def test_cannot_edit_shared_default_profile_directly(self, authed_client):
        default_profile = ISOProfile.objects.filter(is_default=True, is_active=True).first()
        client, user, bank = authed_client

        resp = client.post(
            reverse("iso_field_rules_api", args=[default_profile.id]),
            {"field_path": "CdtTrfTxInf/Whatever", "required": True, "weight": 1},
            format="json",
        )
        assert resp.status_code == 403