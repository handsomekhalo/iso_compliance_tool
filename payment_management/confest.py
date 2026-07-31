"""
Shared fixtures for the RandRail test suite.

Run with:
    DJANGO_SETTINGS_MODULE=iso_compliance.test_settings pytest

These fixtures build a minimal but realistic bank + user + role +
ISO profile so tests exercise the real permission classes
(IsActiveBank, IsAnalystOrAbove, IsInstitutionAdmin) rather than
mocking them away.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from compliance_management.models import Bank, ISOProfile, ISOFieldRule, UserRole, RoleName


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def iso_profile(db):
    """
    Seeds a rule onto the active default ISOProfile template (the one
    Bank.save() clones from). Does NOT create a Bank-facing profile
    directly — each bank's own profile is produced by the clone.
    """
    profile = ISOProfile.objects.filter(is_default=True, is_active=True).order_by("id").first()
    if profile is None:
        profile = ISOProfile.objects.create(
            name="Test CBPR+ Profile",
            message_type="pacs.008",
            version="001.08",
            is_default=True,
            is_active=True,
        )
    ISOFieldRule.objects.get_or_create(
        iso_profile=profile,
        field_path="CdtTrfTxInf/Amt",
        defaults={"required": True, "weight": 5},
    )
    return profile


def _make_bank_user(email, password, role_name, bank_kwargs=None):
    """
    No iso_profile= passed to Bank.objects.create() — this matches
    real register_bank_api usage and lets Bank.save() auto-clone a
    dedicated profile from the default template for this bank.
    """
    user = User.objects.create_user(username=email, email=email, password=password)
    bank = Bank.objects.create(
        name=bank_kwargs.get("name", "Test Bank") if bank_kwargs else "Test Bank",
        contact_email=f"contact-{email}",
        user=user,
    )
    UserRole.objects.create(user=user, role=role_name, bank=bank)
    return user, bank


@pytest.fixture
def institution_admin(db, iso_profile):
    user, bank = _make_bank_user(
        "admin@testbank.co.za", "TestPass123!", RoleName.INSTITUTION_ADMIN,
    )
    return user, bank


@pytest.fixture
def analyst_user(db, iso_profile):
    user, bank = _make_bank_user(
        "analyst@testbank.co.za", "TestPass123!", RoleName.ANALYST,
        bank_kwargs={"name": "Test Bank"},
    )
    return user, bank


@pytest.fixture
def other_bank_admin(db, iso_profile):
    """A second bank, with its own separately-cloned profile — used to prove bank-scoping actually isolates data."""
    user, bank = _make_bank_user(
        "admin@otherbank.co.za", "TestPass123!", RoleName.INSTITUTION_ADMIN,
        bank_kwargs={"name": "Other Bank"},
    )
    return user, bank


@pytest.fixture
def authed_client(api_client, institution_admin):
    user, bank = institution_admin
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client, user, bank